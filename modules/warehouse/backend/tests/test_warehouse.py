import pytest
from fastapi.testclient import TestClient

from core import events
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _login(c, u, p):
    return {"Authorization": "Bearer " + c.post("/api/auth/login",
            json={"username": u, "password": p}).json()["access_token"]}


@pytest.fixture(scope="module")
def admin(client):
    return _login(client, "admin", "admin12345")


@pytest.fixture(scope="module")
def seed(client, admin):
    def mk(url, body):
        r = client.post(url, headers=admin, json=body)
        assert r.status_code == 201, r.text
        return r.json()["id"]
    return dict(
        wa=mk("/api/masterdata/locations", {"name": "WH-A", "type": "warehouse"}),
        wb=mk("/api/masterdata/locations", {"name": "WH-B", "type": "warehouse"}),
        shop=mk("/api/masterdata/locations", {"name": "Shop", "type": "customer"}),
        prod=mk("/api/masterdata/products", {"sku": "WP1", "name": "Wh product", "price": "100"}),
        prod2=mk("/api/masterdata/products", {"sku": "WP2", "name": "Other", "price": "100"}),
        cust=mk("/api/masterdata/customers", {"code": "WC1", "name": "Wh cust"}),
    )


def stock(client, admin, loc, prod):
    r = client.get(f"/api/warehouse/stock?location_id={loc}&product_id={prod}", headers=admin).json()
    return r["items"][0] if r["items"] else None


def test_receipt_issue_adjust_transfer(client, admin, seed):
    H, s = admin, seed
    p = dict(product_id=s["prod2"])
    assert client.post("/api/warehouse/receipts", headers=H,
                       json={**p, "location_id": s["shop"], "quantity": "5"}).status_code == 422  # aguulah bish
    assert client.post("/api/warehouse/receipts", headers=H,
                       json={**p, "location_id": s["wa"], "quantity": "0"}).status_code == 422
    r = client.post("/api/warehouse/receipts", headers=H, json={**p, "location_id": s["wa"], "quantity": "10"})
    assert r.status_code == 201 and float(r.json()["balance_after"]) == 10

    assert client.post("/api/warehouse/issues", headers=H,
                       json={**p, "location_id": s["wa"], "quantity": "11"}).status_code == 409
    assert client.post("/api/warehouse/issues", headers=H,
                       json={**p, "location_id": s["wa"], "quantity": "2"}).status_code == 201
    assert client.post("/api/warehouse/adjustments", headers=H,
                       json={**p, "location_id": s["wa"], "quantity": "0", "note": "x"}).status_code == 422
    assert client.post("/api/warehouse/adjustments", headers=H,
                       json={**p, "location_id": s["wa"], "quantity": "-1", "note": "toollogo"}).status_code == 201

    tr = client.post("/api/warehouse/transfers", headers=H,
                     json={**p, "from_location_id": s["wa"], "to_location_id": s["wb"], "quantity": "3"})
    assert tr.status_code == 201 and [m["type"] for m in tr.json()] == ["transfer_out", "transfer_in"]
    assert client.post("/api/warehouse/transfers", headers=H,
                       json={**p, "from_location_id": s["wa"], "to_location_id": s["wa"], "quantity": "1"}).status_code == 422

    assert float(stock(client, H, s["wa"], s["prod2"])["on_hand"]) == 4   # 10-2-1-3
    assert float(stock(client, H, s["wb"], s["prod2"])["on_hand"]) == 3
    av = client.get(f"/api/warehouse/availability/{s['prod2']}", headers=H).json()
    assert float(av["available"]) == 7
    mv = client.get(f"/api/warehouse/movements?product_id={s['prod2']}", headers=H).json()
    assert mv["total"] == 5   # in, out, adjust, transfer_out, transfer_in


def test_low_stock_and_roles(client, admin, seed):
    s = seed
    st = stock(client, admin, s["wa"], s["prod2"])
    client.patch(f"/api/warehouse/stock/{st['id']}", headers=admin, json={"min_level": "10"})
    low = client.get("/api/warehouse/stock?low_only=true", headers=admin).json()
    assert any(i["id"] == st["id"] for i in low["items"])

    for u, role in (("whw", "warehouse"), ("drw", "driver"), ("acw", "accountant")):
        client.post("/api/auth/users", headers=admin, json={"username": u, "password": "password1", "role": role})
    wh, dr, ac = (_login(client, u, "password1") for u in ("whw", "drw", "acw"))
    body = {"location_id": s["wa"], "product_id": s["prod2"], "quantity": "1"}
    assert client.post("/api/warehouse/receipts", headers=wh, json=body).status_code == 201
    assert client.post("/api/warehouse/receipts", headers=dr, json=body).status_code == 403
    assert client.get("/api/warehouse/stock", headers=ac).status_code == 403
    assert client.get("/api/warehouse/stock").status_code == 401


def _order(client, admin, seed, qty):
    r = client.post("/api/orders", headers=admin, json={
        "customer_id": seed["cust"], "lines": [{"product_id": seed["prod"], "quantity": str(qty)}]})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _status(client, admin, oid, to):
    r = client.post(f"/api/orders/{oid}/status", headers=admin, json={"to": to})
    assert r.status_code == 200, r.text


def test_reserve_cancel_then_shortage_retry_ship(client, admin, seed):
    s, H = seed, admin
    for loc, q in ((s["wa"], "10"), (s["wb"], "4")):
        client.post("/api/warehouse/receipts", headers=H,
                    json={"location_id": loc, "product_id": s["prod"], "quantity": q})

    # 1) confirm -> reserve (best-fit: 5 hureh, WH-A(10) 1 aguulahaas)
    o1 = _order(client, H, s, 5)
    _status(client, H, o1, "confirmed")
    res = client.get(f"/api/warehouse/orders/{o1}/reservations", headers=H).json()
    assert [(r["status"], r["location_id"]) for r in res] == [("active", s["wa"])]
    st = stock(client, H, s["wa"], s["prod"])
    assert float(st["reserved"]) == 5 and float(st["available"]) == 5

    # 2) cancel -> release
    _status(client, H, o1, "cancelled")
    assert float(stock(client, H, s["wa"], s["prod"])["reserved"]) == 0
    assert client.get(f"/api/warehouse/orders/{o1}/reservations", headers=H).json()[0]["status"] == "released"

    # 3) 30 shirheg zahialga: 14 l baina -> 14 reserve, 16 short, shortage event
    got = []
    saved = events.snapshot()
    events.subscribe("stock.shortage")(lambda p: got.append(p))
    o2 = _order(client, H, s, 30)
    _status(client, H, o2, "confirmed")
    assert len(got) == 1 and got[0]["shortages"] == [{"product_id": s["prod"], "quantity": "16.000"}]
    res = client.get(f"/api/warehouse/orders/{o2}/reservations", headers=H).json()
    assert sorted(r["status"] for r in res) == ["active", "active", "short"]
    assert float(client.get(f"/api/warehouse/availability/{s['prod']}", headers=H).json()["available"]) == 0

    # 4) idempotent: 2 dahin retry (uldegdel baihgui) -> short urgeljlene, event garna
    r = client.post(f"/api/warehouse/orders/{o2}/reserve", headers=H)
    assert r.status_code == 200 and "short" in [x["status"] for x in r.json()]
    assert len(got) == 2

    # 5) 20 nemeed retry -> short arilna
    client.post("/api/warehouse/receipts", headers=H,
                json={"location_id": s["wa"], "product_id": s["prod"], "quantity": "20"})
    r = client.post(f"/api/warehouse/orders/{o2}/reserve", headers=H).json()
    assert all(x["status"] == "active" for x in r) and sum(float(x["quantity"]) for x in r) == 30
    assert len(got) == 2
    events.restore(saved)

    # 6) picking -> shipped: stock-oos hasna
    _status(client, H, o2, "picking")
    _status(client, H, o2, "shipped")
    a, b = stock(client, H, s["wa"], s["prod"]), stock(client, H, s["wb"], s["prod"])
    assert float(a["on_hand"]) == 4 and float(a["reserved"]) == 0   # 10+20-26
    assert float(b["on_hand"]) == 0 and float(b["reserved"]) == 0
    res = client.get(f"/api/warehouse/orders/{o2}/reservations", headers=H).json()
    assert {x["status"] for x in res} == {"consumed"}
    mv = client.get(f"/api/warehouse/movements?ref_type=order&ref_id={o2}", headers=H).json()
    assert mv["total"] == 3 and all(m["type"] == "out" for m in mv["items"])


def test_cannot_issue_reserved_stock(client, admin, seed):
    s, H = seed, admin
    client.post("/api/warehouse/receipts", headers=H,
                json={"location_id": s["wb"], "product_id": s["prod"], "quantity": "6"})
    o = _order(client, H, s, 6)
    _status(client, H, o, "confirmed")
    # WH-B: on_hand 6, reserved 6 -> gar aar zarlagalj bolohgui
    r = client.post("/api/warehouse/issues", headers=H,
                    json={"location_id": s["wb"], "product_id": s["prod"], "quantity": "1"})
    assert float(stock(client, H, s["wb"], s["prod"])["reserved"]) == 6
    assert r.status_code == 409
