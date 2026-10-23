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
    def post(url, body, code=201):
        r = client.post(url, headers=admin, json=body)
        assert r.status_code == code, r.text
        return r.json()["id"]
    u1 = post("/api/auth/users", {"username": "trdrv1", "password": "password1", "role": "driver"})
    u2 = post("/api/auth/users", {"username": "trdrv2", "password": "password1", "role": "driver"})
    return dict(
        v_small=post("/api/transport/vehicles", {"plate_no": "TT-0001UBA", "capacity_kg": 100}),
        v_big=post("/api/transport/vehicles", {"plate_no": "TT-0002UBA", "capacity_kg": 1000}),
        v_big2=post("/api/transport/vehicles", {"plate_no": "TT-0003UBA", "capacity_kg": 1000}),
        d1=post("/api/transport/drivers", {"full_name": "Bat", "user_id": u1}),
        d2=post("/api/transport/drivers", {"full_name": "Dorj", "user_id": u2}),
        d3=post("/api/transport/drivers", {"full_name": "Naraa"}),
        cust=post("/api/masterdata/customers", {"code": "TC1", "name": "Tr cust"}),
        loc=post("/api/masterdata/locations", {"name": "Tr shop", "type": "customer", "lat": 47.9, "lng": 106.9}),
        prod=post("/api/masterdata/products", {"sku": "TP1", "name": "Heavy", "weight_kg": 10, "price": "100"}),
        u_drv1=u1,
    )


def mk_order(client, admin, seed, qty, loc=True, upto="shipped"):
    body = {"customer_id": seed["cust"], "lines": [{"product_id": seed["prod"], "quantity": str(qty)}]}
    if loc:
        body["delivery_location_id"] = seed["loc"]
    oid = client.post("/api/orders", headers=admin, json=body).json()["id"]
    for st in ("confirmed", "picking", "shipped"):
        client.post(f"/api/orders/{oid}/status", headers=admin, json={"to": st})
        if st == upto:
            break
    return oid


def shipment(client, admin, oid):
    items = client.get(f"/api/transport/shipments?order_id={oid}", headers=admin).json()["items"]
    return items[0] if items else None


def order_status(client, admin, oid):
    return client.get(f"/api/orders/{oid}", headers=admin).json()["status"]


def test_vehicle_driver_crud(client, admin, seed):
    H = admin
    assert client.post("/api/transport/vehicles", headers=H, json={"plate_no": "TT-0001UBA"}).status_code == 409
    assert client.post("/api/transport/drivers", headers=H,
                       json={"full_name": "dup", "user_id": seed["u_drv1"]}).status_code == 409
    assert client.post("/api/transport/drivers", headers=H,
                       json={"full_name": "ghost", "user_id": 99999}).status_code == 422
    assert client.get("/api/transport/vehicles?q=TT-0002", headers=H).json()["total"] == 1
    assert client.patch(f"/api/transport/drivers/{seed['d3']}", headers=H,
                        json={"phone": "99001122"}).json()["phone"] == "99001122"


def test_shipment_created_from_order_picking(client, admin, seed):
    oid = mk_order(client, admin, seed, 5, upto="confirmed")
    assert shipment(client, admin, oid) is None          # picking-ees omno shipment gui
    client.post(f"/api/orders/{oid}/status", headers=admin, json={"to": "picking"})
    s = shipment(client, admin, oid)
    assert s["status"] == "pending" and s["ready"] is False and s["weight_kg"] == 50
    client.post(f"/api/orders/{oid}/status", headers=admin, json={"to": "shipped"})
    assert shipment(client, admin, oid)["ready"] is True


def test_capacity_location_and_conflicts(client, admin, seed):
    H = admin
    o1, o2 = mk_order(client, H, seed, 5), mk_order(client, H, seed, 8)   # 50kg + 80kg
    s1, s2 = shipment(client, H, o1)["id"], shipment(client, H, o2)["id"]
    base = {"driver_id": seed["d1"], "planned_date": "2030-01-10"}

    r = client.post("/api/transport/trips", headers=H, json={**base, "vehicle_id": seed["v_small"], "shipment_ids": [s1, s2]})
    assert r.status_code == 409 and "Achaa" in r.json()["error"]["message"]      # 130kg > 100kg

    no_loc = mk_order(client, H, seed, 1, loc=False)
    sn = shipment(client, H, no_loc)["id"]
    assert client.post("/api/transport/trips", headers=H, json={**base, "vehicle_id": seed["v_big"],
                       "shipment_ids": [sn]}).status_code == 422                # hayag baihgui

    ok = client.post("/api/transport/trips", headers=H, json={**base, "vehicle_id": seed["v_big"], "shipment_ids": [s1, s2]})
    assert ok.status_code == 201, ok.text
    t = ok.json()
    assert t["trip_no"].startswith("TRP-203001") and t["total_weight_kg"] == 130
    assert [x["stop_sequence"] for x in t["stops"]] == [1, 2]

    # ayn odor ayn mashin / jolooch
    assert client.post("/api/transport/trips", headers=H, json={**base, "vehicle_id": seed["v_big"]}).status_code == 409
    assert client.post("/api/transport/trips", headers=H, json={**base, "vehicle_id": seed["v_big2"]}).status_code == 409
    # idevhtei trip-tei mashin/jolooch ustgah bolomjgui
    assert client.delete(f"/api/transport/vehicles/{seed['v_big']}", headers=H).status_code == 409
    assert client.delete(f"/api/transport/drivers/{seed['d1']}", headers=H).status_code == 409

    # reorder + remove + cancel
    r = client.put(f"/api/transport/trips/{t['id']}/order", headers=H, json={"shipment_ids": [s2, s1]})
    assert [x["id"] for x in r.json()["stops"]] == [s2, s1]
    assert client.put(f"/api/transport/trips/{t['id']}/order", headers=H, json={"shipment_ids": [s1]}).status_code == 422
    r = client.delete(f"/api/transport/trips/{t['id']}/shipments/{s2}", headers=H).json()
    assert [x["id"] for x in r["stops"]] == [s1] and r["stops"][0]["stop_sequence"] == 1
    assert shipment(client, H, o2)["status"] == "pending"
    c = client.post(f"/api/transport/trips/{t['id']}/cancel", headers=H).json()
    assert c["status"] == "cancelled" and shipment(client, H, o1)["status"] == "pending"
    assert client.post(f"/api/transport/trips/{t['id']}/start", headers=H).status_code == 409


def test_start_requires_ready(client, admin, seed):
    H = admin
    oid = mk_order(client, H, seed, 2, upto="picking")                # shipped bish -> ready=False
    sid = shipment(client, H, oid)["id"]
    t = client.post("/api/transport/trips", headers=H, json={"vehicle_id": seed["v_big"], "driver_id": seed["d1"],
                    "planned_date": "2030-02-01", "shipment_ids": [sid]}).json()
    assert client.post(f"/api/transport/trips/{t['id']}/start", headers=H).status_code == 409
    client.post(f"/api/orders/{oid}/status", headers=H, json={"to": "shipped"})
    assert client.post(f"/api/transport/trips/{t['id']}/start", headers=H).status_code == 200
    client.post(f"/api/transport/shipments/{sid}/deliver", headers=H)


def test_full_delivery_flow_events_and_driver_rights(client, admin, seed):
    H = admin
    got = []
    saved = events.snapshot()
    for e in ("trip.started", "shipment.delivered", "shipment.failed", "trip.completed"):
        events.subscribe(e)(lambda p, e=e: got.append(e))

    o1, o2 = mk_order(client, H, seed, 3), mk_order(client, H, seed, 4)
    s1, s2 = shipment(client, H, o1)["id"], shipment(client, H, o2)["id"]
    t = client.post("/api/transport/trips", headers=H, json={"vehicle_id": seed["v_big2"], "driver_id": seed["d1"],
                    "planned_date": "2030-03-01", "shipment_ids": [s1, s2]}).json()
    drv1, drv2 = _login(client, "trdrv1", "password1"), _login(client, "trdrv2", "password1")

    assert client.post(f"/api/transport/shipments/{s1}/deliver", headers=H).status_code == 409   # trip ehleegui
    assert client.post(f"/api/transport/trips/{t['id']}/start", headers=drv1).status_code == 403  # jolooch ehluulehgui
    assert client.post(f"/api/transport/trips/{t['id']}/start", headers=H).status_code == 200

    assert client.post(f"/api/transport/shipments/{s1}/deliver", headers=drv2).status_code == 403  # busdiin trip
    r = client.post(f"/api/transport/shipments/{s1}/deliver", headers=drv1, json={"note": "Huleen avlaa"})
    assert r.status_code == 200 and r.json()["status"] == "delivered"
    assert order_status(client, H, o1) == "delivered"                                  # Orders-iin handler
    assert client.get(f"/api/transport/trips/{t['id']}", headers=H).json()["status"] == "in_progress"

    r = client.post(f"/api/transport/shipments/{s2}/fail", headers=drv1, json={"reason": "Hariltsagch gertee baihgui"})
    assert r.status_code == 200 and r.json()["failed_reason"]
    assert order_status(client, H, o2) == "shipped"                                    # busad ur dun gui
    done = client.get(f"/api/transport/trips/{t['id']}", headers=H).json()
    assert done["status"] == "completed" and done["completed_at"]
    assert got == ["trip.started", "shipment.delivered", "shipment.failed", "trip.completed"]
    events.restore(saved)

    mine = client.get("/api/transport/my/trips", headers=drv1).json()
    assert any(x["id"] == t["id"] for x in mine["items"])
    assert client.get("/api/transport/my/trips", headers=drv2).json()["total"] == 0

    # Amjiltgui shipment-g shine trip-d dahin tavih
    t2 = client.post("/api/transport/trips", headers=H, json={"vehicle_id": seed["v_big"], "driver_id": seed["d2"],
                     "planned_date": "2030-03-02", "shipment_ids": [s2]})
    assert t2.status_code == 201 and t2.json()["stops"][0]["status"] == "assigned"
    assert t2.json()["stops"][0]["failed_reason"] is None


def test_order_cancel_cancels_shipment(client, admin, seed):
    H = admin
    oid = mk_order(client, H, seed, 1, upto="picking")
    assert shipment(client, H, oid)["status"] == "pending"
    client.post(f"/api/orders/{oid}/status", headers=H, json={"to": "cancelled"})
    assert shipment(client, H, oid)["status"] == "cancelled"
    sid = shipment(client, H, oid)["id"]
    assert client.post("/api/transport/trips", headers=H, json={"vehicle_id": seed["v_big"], "driver_id": seed["d3"],
                       "planned_date": "2030-04-01", "shipment_ids": [sid]}).status_code == 409


def test_roles(client, admin, seed):
    assert client.get("/api/transport/vehicles").status_code == 401
    drv = _login(client, "trdrv1", "password1")
    assert client.get("/api/transport/vehicles", headers=drv).status_code == 200
    assert client.post("/api/transport/vehicles", headers=drv, json={"plate_no": "X"}).status_code == 403
