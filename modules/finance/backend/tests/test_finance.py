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


@pytest.fixture(scope="module")
def accountant(client, admin):
    r = client.post("/api/auth/users", headers=admin, json={
        "username": "fin_acc", "password": "acc-pass-123", "role": "accountant"})
    assert r.status_code == 201, r.text
    return _login(client, "fin_acc", "acc-pass-123")


def _invoice(client, h, customer="Fin Cust", amount="1000.50"):
    return client.post("/api/finance/invoices", headers=h, json={
        "customer": customer, "issued": "2026-10-01", "due": "2026-10-31", "amount": amount})


def test_invoice_create_and_list_shape(client, accountant):
    r = _invoice(client, accountant)
    assert r.status_code == 201, r.text
    inv = r.json()
    assert inv["number"] == f"НХ-2026-{inv['id']:04d}"
    assert inv["customer"] == "Fin Cust" and inv["paid"] == 0 and inv["amount"] == 1000.5
    lst = client.get("/api/finance/invoices", headers=accountant).json()
    assert isinstance(lst, list) and any(i["id"] == inv["id"] for i in lst)
    # ijil ner dahin ashiglahad kharitsagch davhardahgui
    assert _invoice(client, accountant).json()["customerId"] == inv["customerId"]


def test_invoice_validation(client, accountant):
    r = client.post("/api/finance/invoices", headers=accountant, json={
        "customer": "X", "issued": "2026-10-10", "due": "2026-10-01", "amount": "5"})
    assert r.status_code == 422
    r = client.post("/api/finance/invoices", headers=accountant, json={
        "issued": "2026-10-01", "due": "2026-10-31", "amount": "5"})
    assert r.status_code == 422
    assert _invoice(client, accountant, amount="0").status_code == 422


def test_payments_partial_full_overpay(client, accountant):
    inv = _invoice(client, accountant, "Pay Cust", "1000").json()

    def pay(amount, method="transfer"):
        return client.post("/api/finance/payments", headers=accountant, json={
            "invoiceId": inv["id"], "date": "2026-10-05", "amount": amount, "method": method})

    assert pay("400", "cash").status_code == 201
    assert client.get(f"/api/finance/invoices/{inv['id']}", headers=accountant).json()["paid"] == 400
    assert pay("700").status_code == 422          # uldegdel 600
    assert pay("600", "card").status_code == 201
    assert pay("1").status_code == 409            # buten tulugdsun
    assert pay("10", "bitcoin").status_code == 422
    pays = client.get(f"/api/finance/payments?invoice_id={inv['id']}", headers=accountant).json()
    assert [p["method"] for p in pays] == ["cash", "card"]
    bad = client.post("/api/finance/payments", headers=accountant, json={
        "invoiceId": 99999, "date": "2026-10-05", "amount": "1", "method": "cash"})
    assert bad.status_code == 404


def test_expenses(client, accountant):
    r = client.post("/api/finance/expenses", headers=accountant, json={
        "date": "2026-10-02", "category": "Түлш", "vendor": "Петровис", "amount": 21500000})
    assert r.status_code == 201 and r.json()["status"] == "paid"
    client.post("/api/finance/expenses", headers=accountant, json={
        "date": "2026-10-03", "category": "Татвар", "vendor": "Гааль", "amount": 5, "status": "pending"})
    pend = client.get("/api/finance/expenses?status=pending", headers=accountant).json()
    assert pend and all(e["status"] == "pending" for e in pend)
    assert client.post("/api/finance/expenses", headers=accountant, json={
        "date": "2026-10-02", "category": "x", "vendor": "y", "amount": 1, "status": "?"}).status_code == 422


def test_permissions(client, admin):
    client.post("/api/auth/users", headers=admin, json={
        "username": "fin_disp", "password": "disp-pass-123", "role": "dispatcher"})
    d = _login(client, "fin_disp", "disp-pass-123")
    assert client.get("/api/finance/invoices", headers=d).status_code == 403
    assert client.get("/api/finance/invoices").status_code == 401


def test_invoice_created_when_order_delivered(client, admin):
    cust = client.post("/api/masterdata/customers", headers=admin,
                       json={"code": "FC9", "name": "Delivered Cust"}).json()["id"]
    prod = client.post("/api/masterdata/products", headers=admin,
                       json={"sku": "FP9", "name": "Salt", "price": "1500"}).json()["id"]
    o = client.post("/api/orders", headers=admin, json={
        "customer_id": cust, "lines": [{"product_id": prod, "quantity": "4"}]}).json()
    for s in ("confirmed", "picking", "shipped", "delivered"):
        assert client.post(f"/api/orders/{o['id']}/status", headers=admin, json={"to": s}).status_code == 200
    invs = client.get(f"/api/finance/invoices?order_id={o['id']}", headers=admin).json()
    assert len(invs) == 1
    assert invs[0]["amount"] == 6000 and invs[0]["customerId"] == cust and invs[0]["paid"] == 0
    assert invs[0]["number"].startswith("НХ-")
