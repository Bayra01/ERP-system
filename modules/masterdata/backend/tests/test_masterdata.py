import pytest
from fastapi.testclient import TestClient

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


def test_requires_auth(client):
    assert client.get("/api/masterdata/customers").status_code == 401


def test_customer_crud_and_soft_delete(client, admin):
    r = client.post("/api/masterdata/customers", headers=admin,
                    json={"code": "C001", "name": "Nomin Trade", "phone": "99112233"})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert client.post("/api/masterdata/customers", headers=admin,
                       json={"code": "C001", "name": "dup"}).status_code == 409

    assert client.patch(f"/api/masterdata/customers/{cid}", headers=admin,
                        json={"name": "Nomin Trade LLC"}).json()["name"] == "Nomin Trade LLC"
    res = client.get("/api/masterdata/customers?q=nomin", headers=admin).json()
    assert res["total"] == 1

    assert client.delete(f"/api/masterdata/customers/{cid}", headers=admin).status_code == 204
    assert client.get(f"/api/masterdata/customers/{cid}", headers=admin).status_code == 404
    assert client.get("/api/masterdata/customers", headers=admin).json()["total"] == 0


def test_product_validation(client, admin):
    r = client.post("/api/masterdata/products", headers=admin,
                    json={"sku": "P-1", "name": "Water 1L", "unit": "pcs",
                          "weight_kg": 1.0, "price": "1500.50"})
    assert r.status_code == 201, r.text
    assert float(r.json()["price"]) == 1500.5
    assert client.post("/api/masterdata/products", headers=admin,
                       json={"sku": "P-2", "name": "bad", "price": -1}).status_code == 422
    assert client.post("/api/masterdata/products", headers=admin,
                       json={"sku": "P-1", "name": "dup"}).status_code == 409


def test_location_rules(client, admin):
    cid = client.post("/api/masterdata/customers", headers=admin,
                      json={"code": "C002", "name": "Shop"}).json()["id"]
    ok = client.post("/api/masterdata/locations", headers=admin,
                     json={"name": "Shop UB", "type": "customer", "lat": 47.9186,
                           "lng": 106.9177, "customer_id": cid})
    assert ok.status_code == 201, ok.text
    # buruu koordinat, olddoggui customer
    assert client.post("/api/masterdata/locations", headers=admin,
                       json={"name": "x", "lat": 200}).status_code == 422
    assert client.post("/api/masterdata/locations", headers=admin,
                       json={"name": "x", "customer_id": 9999}).status_code == 404
    # locationtoi customer-g ustgah bolomjgui
    assert client.delete(f"/api/masterdata/customers/{cid}", headers=admin).status_code == 409
    flt = client.get(f"/api/masterdata/locations?customer_id={cid}&type=customer", headers=admin).json()
    assert flt["total"] == 1


def test_roles(client, admin):
    client.post("/api/auth/users", headers=admin,
                json={"username": "acc1", "password": "password1", "role": "accountant"})
    client.post("/api/auth/users", headers=admin,
                json={"username": "disp2", "password": "password1", "role": "dispatcher"})
    acc = _login(client, "acc1", "password1")
    assert client.get("/api/masterdata/customers", headers=acc).status_code == 200
    assert client.post("/api/masterdata/customers", headers=acc,
                       json={"code": "Z", "name": "z"}).status_code == 403
    disp = _login(client, "disp2", "password1")
    assert client.post("/api/masterdata/customers", headers=disp,
                       json={"code": "C900", "name": "ok"}).status_code == 201
