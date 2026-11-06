import pytest
from fastapi.testclient import TestClient

from core import events
from core.permissions import Role, has_permission
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # lifespan -> table + first admin
        yield c


def login(client, u="admin", p="admin12345"):
    r = client.post("/api/auth/login", json={"username": u, "password": p})
    return r


def H(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy"}


def test_login_bad_password(client):
    r = login(client, p="wrong")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_admin_flow(client):
    token = login(client).json()["access_token"]
    me = client.get("/api/auth/me", headers=H(token)).json()
    assert me["username"] == "admin" and me["role"] == "admin"

    r = client.post("/api/auth/users", headers=H(token),
                    json={"username": "disp1", "password": "password1", "role": "dispatcher"})
    assert r.status_code == 201
    assert client.post("/api/auth/users", headers=H(token),
                       json={"username": "disp1", "password": "password1"}).status_code == 409

    lst = client.get("/api/auth/users?page=1&size=10", headers=H(token)).json()
    assert lst["total"] == 2


def test_rbac_non_admin_forbidden(client):
    token = login(client, "disp1", "password1").json()["access_token"]
    r = client.get("/api/auth/users", headers=H(token))
    assert r.status_code == 403


def test_deactivated_user_cannot_login(client):
    admin = login(client).json()["access_token"]
    uid = client.post("/api/auth/users", headers=H(admin),
                      json={"username": "tmp1", "password": "password1"}).json()["id"]
    client.patch(f"/api/auth/users/{uid}", headers=H(admin), json={"is_active": False})
    assert login(client, "tmp1", "password1").status_code == 401


def test_permissions():
    assert has_permission(Role.ADMIN, "anything:else")
    assert has_permission(Role.ACCOUNTANT, "finance:write")
    assert not has_permission(Role.DRIVER, "finance:write")


def test_event_bus():
    got = []
    saved = events.snapshot()
    events.clear()
    events.subscribe("t.evt")(lambda p: got.append(p))
    events.subscribe("t.evt")(lambda p: 1 / 0)  # aldaa busdad n nölöölöhgui
    events.publish("t.evt", {"a": 1})
    assert got == [{"a": 1}]
    events.restore(saved)
