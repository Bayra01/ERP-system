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
    cust = client.post("/api/masterdata/customers", headers=admin,
                       json={"code": "OC1", "name": "Order Cust"}).json()["id"]
    other = client.post("/api/masterdata/customers", headers=admin,
                        json={"code": "OC2", "name": "Other Cust"}).json()["id"]
    p1 = client.post("/api/masterdata/products", headers=admin,
                     json={"sku": "OP1", "name": "Rice", "price": "2000"}).json()["id"]
    p2 = client.post("/api/masterdata/products", headers=admin,
                     json={"sku": "OP2", "name": "Oil", "price": "5500.50"}).json()["id"]
    loc = client.post("/api/masterdata/locations", headers=admin,
                      json={"name": "OC1 shop", "type": "customer", "customer_id": cust}).json()["id"]
    return dict(cust=cust, other=other, p1=p1, p2=p2, loc=loc)


def _create(client, admin, seed, **kw):
    body = {"customer_id": seed["cust"], "delivery_location_id": seed["loc"],
            "lines": [{"product_id": seed["p1"], "quantity": "3"},
                      {"product_id": seed["p2"], "quantity": "2", "unit_price": "5000"}]}
    body.update(kw)
    return client.post("/api/orders", headers=admin, json=body)


def test_create_totals_and_number(client, admin, seed):
    r = _create(client, admin, seed)
    assert r.status_code == 201, r.text
    o = r.json()
    assert o["status"] == "draft" and o["order_no"].startswith("ORD-")
    assert float(o["total_amount"]) == 3 * 2000 + 2 * 5000  # product price + override
    assert len(o["lines"]) == 2 and o["history"][0]["to_status"] == "draft"


def test_validation(client, admin, seed):
    assert _create(client, admin, seed, lines=[]).status_code == 422
    assert _create(client, admin, seed, customer_id=99999).status_code == 422
    assert _create(client, admin, seed, customer_id=seed["other"]).status_code == 422  # location mismatch
    bad = _create(client, admin, seed, lines=[{"product_id": 99999, "quantity": "1"}])
    assert bad.status_code == 422
    assert _create(client, admin, seed, lines=[{"product_id": seed["p1"], "quantity": "0"}]).status_code == 422


def test_update_only_draft(client, admin, seed):
    o = _create(client, admin, seed).json()
    r = client.patch(f"/api/orders/{o['id']}", headers=admin,
                     json={"notes": "urgent", "lines": [{"product_id": seed["p1"], "quantity": "10"}]})
    assert r.status_code == 200, r.text
    assert float(r.json()["total_amount"]) == 20000 and len(r.json()["lines"]) == 1
    client.post(f"/api/orders/{o['id']}/status", headers=admin, json={"to": "confirmed"})
    assert client.patch(f"/api/orders/{o['id']}", headers=admin, json={"notes": "x"}).status_code == 409
    assert client.delete(f"/api/orders/{o['id']}", headers=admin).status_code == 409


def test_full_flow_events_and_roles(client, admin, seed):
    # Role-uud
    for u, role in (("wh1", "warehouse"), ("dr1", "driver"), ("ac2", "accountant")):
        client.post("/api/auth/users", headers=admin,
                    json={"username": u, "password": "password1", "role": role})
    wh, dr, ac = (_login(client, u, "password1") for u in ("wh1", "dr1", "ac2"))

    got = []
    saved = events.snapshot()
    events.clear()
    for e in ("confirmed", "picking", "shipped", "delivered", "cancelled"):
        events.subscribe(f"order.{e}")(lambda p, e=e: got.append((e, p)))

    oid = _create(client, admin, seed).json()["id"]
    st = lambda h, to: client.post(f"/api/orders/{oid}/status", headers=h, json={"to": to})

    assert st(admin, "shipped").status_code == 409          # draft -> shipped bolohgui
    assert st(wh, "confirmed").status_code == 403           # warehouse batalgaajuulah erhgui
    assert st(admin, "confirmed").status_code == 200
    assert st(dr, "picking").status_code == 403             # driver picking hiih erhgui
    assert st(wh, "picking").status_code == 200
    assert st(wh, "shipped").status_code == 200
    assert st(ac, "delivered").status_code == 403
    r = st(dr, "delivered")
    assert r.status_code == 200 and r.json()["status"] == "delivered"
    assert st(admin, "cancelled").status_code == 409        # terminal

    assert [e for e, _ in got] == ["confirmed", "picking", "shipped", "delivered"]
    payload = got[0][1]
    assert payload["order_id"] == oid and len(payload["lines"]) == 2
    hist = [h["to_status"] for h in client.get(f"/api/orders/{oid}", headers=admin).json()["history"]]
    assert hist == ["draft", "confirmed", "picking", "shipped", "delivered"]
    events.restore(saved)


def test_cancel_list_filters_delete(client, admin, seed):
    a = _create(client, admin, seed).json()["id"]
    b = _create(client, admin, seed).json()["id"]
    client.post(f"/api/orders/{a}/status", headers=admin, json={"to": "cancelled", "note": "oorchlolt"})
    res = client.get("/api/orders?status=cancelled", headers=admin).json()
    assert any(i["id"] == a for i in res["items"]) and all(i["status"] == "cancelled" for i in res["items"])
    assert client.get(f"/api/orders?customer_id={seed['cust']}&size=2", headers=admin).json()["size"] == 2
    assert client.delete(f"/api/orders/{b}", headers=admin).status_code == 204
    assert client.get(f"/api/orders/{b}", headers=admin).status_code == 404
    assert client.get("/api/orders/health").json()["status"] == "ok"
