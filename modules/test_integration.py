"""Buten urgal: masterdata -> uldegdel -> zahialga -> reserve -> shipment -> trip -> hurgelt
-> nehemjleh -> tulbur. Bukh modul event-eer holbogdson esehiig shalgana."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as client:
        r = client.post("/api/auth/login", json={"username": "admin", "password": "admin12345"})
        assert r.status_code == 200, r.text
        client.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
        yield client


def ok(r, code=200):
    assert r.status_code == code, r.text
    return r.json() if r.content else None


def test_auth_errors(c):
    anon = TestClient(app)
    assert anon.get("/api/orders").status_code == 401
    r = anon.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthorized"


def test_full_flow(c):
    md = "/api/masterdata"
    wh = ok(c.post(f"{md}/locations", json={"name": "Tuv aguulah", "type": "warehouse",
                                           "lat": 47.92, "lng": 106.92}), 201)
    cust = ok(c.post(f"{md}/customers", json={"name": "Barilga LLC"}), 201)
    assert cust["code"] == f"C-{cust['id']}"
    dest = ok(c.post(f"{md}/locations", json={"name": "Talbai", "customer_id": cust["id"],
                                             "lat": 49.48, "lng": 105.96}), 201)
    prod = ok(c.post(f"{md}/products", json={"sku": "CEM-50", "name": "Cement", "price": "15000",
                                            "weight_kg": 50}), 201)
    assert c.post(f"{md}/products", json={"sku": "CEM-50", "name": "x"}).status_code == 409

    # uldegdel
    ok(c.post("/api/warehouse/movements", json={"location_id": wh["id"], "product_id": prod["id"],
                                               "type": "in", "quantity": "100"}), 201)
    r = c.post("/api/warehouse/movements", json={"location_id": wh["id"], "product_id": prod["id"],
                                                "type": "out", "quantity": "1000"})
    assert r.status_code == 409

    # zahialga
    order = ok(c.post("/api/orders", json={"customer_id": cust["id"],
                                          "delivery_location_id": dest["id"],
                                          "lines": [{"product_id": prod["id"], "quantity": "10"}]}), 201)
    assert order["status"] == "draft" and float(order["total_amount"]) == 150000
    assert order["order_no"].startswith("ORD-")
    oid = order["id"]
    page = ok(c.get("/api/orders", params={"status": "draft"}))
    assert page["total"] >= 1

    def move(to):
        return ok(c.post(f"/api/orders/{oid}/status", json={"to": to}))

    assert c.post(f"/api/orders/{oid}/status", json={"to": "shipped"}).status_code == 409
    move("confirmed")
    res = ok(c.get("/api/warehouse/reservations", params={"order_id": oid}))
    assert res[0]["status"] == "reserved" and res[0]["location_id"] == wh["id"]
    stock = ok(c.get("/api/warehouse/stock", params={"product_id": prod["id"]}))["items"][0]
    assert stock["reserved"] == 10 and stock["available"] == 90

    move("picking")
    sh = ok(c.get("/api/transport/shipments"))["items"][0]
    assert sh["order_id"] == oid and sh["weight_kg"] == 500 and not sh["ready"]

    move("shipped")
    stock = ok(c.get("/api/warehouse/stock", params={"product_id": prod["id"]}))["items"][0]
    assert stock["on_hand"] == 90 and stock["reserved"] == 0
    sh = ok(c.get(f"/api/transport/shipments/{sh['id']}"))
    assert sh["ready"]

    # teever
    v = ok(c.post("/api/transport/vehicles", json={"plate_no": "UBA 1234", "capacity_kg": 400}), 201)
    d = ok(c.post("/api/transport/drivers", json={"full_name": "B. Bat"}), 201)
    r = c.post("/api/transport/trips", json={"vehicle_id": v["id"], "driver_id": d["id"],
                                             "planned_date": "2026-10-30",
                                             "depot_location_id": wh["id"],
                                             "shipment_ids": [sh["id"]]})
    assert r.status_code == 409  # 500 kg > 400 kg
    ok(c.patch(f"/api/transport/vehicles/{v['id']}", json={"capacity_kg": 10000}))
    trip = ok(c.post("/api/transport/trips", json={"vehicle_id": v["id"], "driver_id": d["id"],
                                                  "planned_date": "2026-10-30",
                                                  "depot_location_id": wh["id"],
                                                  "shipment_ids": [sh["id"]]}), 201)
    assert trip["stops"] == 1 and trip["vehicle_plate"] == "UBA 1234"

    route = ok(c.post(f"/api/routing/trips/{trip['id']}/optimize"))
    assert 150 < route["total_distance_km"] < 250  # UB -> Darkhan ~ 180 km

    trip = ok(c.post(f"/api/transport/trips/{trip['id']}/start"))
    assert trip["status"] == "in_progress"
    ok(c.post(f"/api/transport/shipments/{sh['id']}/deliver"))
    trip = ok(c.get(f"/api/transport/trips/{trip['id']}"))
    assert trip["status"] == "completed"
    assert ok(c.get(f"/api/transport/vehicles"))["items"][0]["status"] == "available"

    # orders -> delivered, finance -> invoice
    assert ok(c.get(f"/api/orders/{oid}"))["status"] == "delivered"
    inv = [i for i in ok(c.get("/api/finance/invoices")) if i["orderId"] == oid][0]
    assert inv["amount"] == 150000 and inv["status"] == "unpaid" and inv["customer"] == "Barilga LLC"

    assert c.post("/api/finance/payments", json={"invoiceId": inv["id"], "amount": 999999}).status_code == 422
    ok(c.post("/api/finance/payments", json={"invoiceId": inv["id"], "amount": 150000}), 201)
    assert ok(c.get(f"/api/finance/invoices/{inv['id']}"))["status"] == "paid"
    assert c.post("/api/finance/payments", json={"invoiceId": inv["id"], "amount": 1}).status_code == 409

    # medegdel
    events = {n["event"] for n in ok(c.get("/api/notifications", params={"size": 50}))["items"]}
    assert {"order.confirmed", "order.delivered", "trip.completed"} <= events


def test_shortage_and_cancel(c):
    md = "/api/masterdata"
    cust = ok(c.post(f"{md}/customers", json={"name": "Short LLC"}), 201)
    prod = ok(c.post(f"{md}/products", json={"sku": "RARE-1", "name": "Rare", "price": "10"}), 201)
    order = ok(c.post("/api/orders", json={"customer_id": cust["id"],
                                          "lines": [{"product_id": prod["id"], "quantity": "5"}]}), 201)
    ok(c.post(f"/api/orders/{order['id']}/status", json={"to": "confirmed"}))
    res = ok(c.get("/api/warehouse/reservations", params={"order_id": order["id"]}))
    assert res[0]["status"] == "short"
    events = [n["event"] for n in ok(c.get("/api/notifications", params={"unread": True}))["items"]]
    assert "stock.shortage" in events
    ok(c.post(f"/api/orders/{order['id']}/status", json={"to": "cancelled"}))
    res = ok(c.get("/api/warehouse/reservations", params={"order_id": order["id"]}))
    assert res[0]["status"] == "released"


def test_finance_manual_invoice_and_expense(c):
    inv = ok(c.post("/api/finance/invoices", json={"customer": "Shine Kharilcagch", "amount": 5000}), 201)
    assert inv["number"].startswith("INV-") and inv["balance"] == 5000
    customers = ok(c.get("/api/masterdata/customers", params={"q": "Shine"}))["items"]
    assert customers[0]["code"].startswith("AUTO-")
    e = ok(c.post("/api/finance/expenses", json={"category": "Fuel", "vendor": "Shell", "amount": 120.5}), 201)
    assert e["amount"] == 120.5


def test_finance_report(c):
    r = ok(c.get("/api/finance/reports/summary"))
    assert {"invoiced", "collected", "expenses", "net", "outstanding", "overdue"} <= set(r["totals"])
    assert len(r["monthly"]) == 6 and r["monthly"][-1]["month"] == r["to"][:7]
    assert [a["bucket"] for a in r["aging"]] == ["current", "1-30", "31-60", "61-90", "90+"]
    assert r["totals"]["outstanding"] >= 5000  # test_finance_manual_invoice
    assert r["expensesByCategory"][0]["category"] == "Fuel"
    assert c.get("/api/finance/reports/summary",
                 params={"date_from": "2026-12-01", "date_to": "2026-01-01"}).status_code == 422


def test_route_sequence(c):
    md = "/api/masterdata"
    wh = ok(c.post(f"{md}/locations", json={"name": "R-depot", "type": "warehouse", "lat": 47.9, "lng": 106.9}), 201)
    cust = ok(c.post(f"{md}/customers", json={"name": "Route LLC"}), 201)
    prod = ok(c.post(f"{md}/products", json={"sku": "R-1", "name": "R", "price": "1"}), 201)
    ok(c.post("/api/warehouse/movements", json={"location_id": wh["id"], "product_id": prod["id"],
                                               "type": "in", "quantity": "10"}), 201)
    ships = []
    for name, lat, lng in [("Far", 49.0, 104.0), ("Near", 47.95, 106.95)]:
        loc = ok(c.post(f"{md}/locations", json={"name": name, "customer_id": cust["id"], "lat": lat, "lng": lng}), 201)
        o = ok(c.post("/api/orders", json={"customer_id": cust["id"], "delivery_location_id": loc["id"],
                                          "lines": [{"product_id": prod["id"], "quantity": "1"}]}), 201)
        for to in ("confirmed", "picking"):
            ok(c.post(f"/api/orders/{o['id']}/status", json={"to": to}))
        ships.append([s for s in ok(c.get("/api/transport/shipments"))["items"] if s["order_id"] == o["id"]][0]["id"])
    v = ok(c.post("/api/transport/vehicles", json={"plate_no": "R-0001"}), 201)
    d = ok(c.post("/api/transport/drivers", json={"full_name": "R driver"}), 201)
    trip = ok(c.post("/api/transport/trips", json={"vehicle_id": v["id"], "driver_id": d["id"],
                                                  "planned_date": "2026-11-01", "depot_location_id": wh["id"],
                                                  "shipment_ids": ships}), 201)
    opt = ok(c.post(f"/api/routing/trips/{trip['id']}/optimize"))
    assert [s["location_name"] for s in opt["stops"]] == ["Near", "Far"]
    assert opt["total_distance_km"] < opt["previous_km"]
    back = ok(c.put(f"/api/routing/trips/{trip['id']}/sequence", json={"shipment_ids": ships}))
    assert [s["location_name"] for s in back["stops"]] == ["Far", "Near"]
    assert back["previous_km"] == opt["total_distance_km"]
    assert c.put(f"/api/routing/trips/{trip['id']}/sequence", json={"shipment_ids": ships[:1]}).status_code == 422


def test_messages(c):
    from core.database import SessionLocal
    from modules.auth.backend.service import create_user
    with SessionLocal() as db:
        create_user(db, "acc1", "acc123", "accountant", "Nyagtlan 1")
    acc = TestClient(app)
    tok = ok(acc.post("/api/auth/login", json={"username": "acc1", "password": "acc123"}))["access_token"]
    acc.headers["Authorization"] = f"Bearer {tok}"

    rec = ok(c.get("/api/notifications/recipients"))
    acc_id = [u for u in rec if u["username"] == "acc1"][0]["id"]
    assert ok(c.post("/api/notifications/send", json={"to_user_id": acc_id, "title": "Nehemjleh",
                                                      "message": "INV shalgana uu"}), 201)["sent"] == 1
    assert ok(c.post("/api/notifications/send", json={"role": "accountant", "title": "Buh nyagtland",
                                                      "message": "Sar haalt"}), 201)["sent"] == 1
    inbox = ok(acc.get("/api/notifications", params={"kind": "message"}))["items"]
    assert len(inbox) == 2 and inbox[0]["sender_name"] == "Administrator"
    ok(acc.post("/api/notifications/send", json={"reply_to": inbox[0]["id"], "title": "Re", "message": "Za"}), 201)
    mine = ok(c.get("/api/notifications", params={"kind": "message", "unread": True}))["items"]
    assert mine[0]["title"] == "Re" and mine[0]["sender_name"] == "Nyagtlan 1"
    sent = ok(c.get("/api/notifications", params={"box": "sent"}))["items"]
    assert {s["recipient_name"] for s in sent} == {"Nyagtlan 1"}
    assert c.post("/api/notifications/send", json={"title": "x", "message": "y"}).status_code == 422


def test_module_login_and_staff(c):
    anon = TestClient(app)
    # Ajiltan nemeh (admin)
    u = ok(c.post("/api/auth/users", json={"username": "wh1", "full_name": "Agualah 1",
                                           "password": "wh1234", "role": "warehouse"}), 201)
    assert u["modules"] == ["orders", "warehouse", "notifications"]
    assert c.post("/api/auth/users", json={"username": "wh1", "password": "xxxxxx"}).status_code == 409

    # Modul burt nevtreh
    r = anon.post("/api/auth/login", json={"username": "wh1", "password": "wh1234", "module": "warehouse"})
    assert r.status_code == 200
    wh_tok = r.json()["access_token"]
    r = anon.post("/api/auth/login", json={"username": "wh1", "password": "wh1234", "module": "finance"})
    assert r.status_code == 403
    err = r.json()["error"]
    assert err["allowed"] == ["orders", "warehouse", "notifications"] and err["role"] == "warehouse"
    assert anon.post("/api/auth/login", json={"username": "wh1", "password": "x", "module": "x"}).status_code == 422

    # Ajiltan admin API-g ashiglaj chadahgui, uuriin nuuts ugee solino
    h = {"Authorization": f"Bearer {wh_tok}"}
    assert anon.get("/api/auth/users", headers=h).status_code == 403
    assert anon.post("/api/auth/me/password", headers=h,
                     json={"old_password": "bad", "new_password": "newpass1"}).status_code == 422
    assert anon.post("/api/auth/me/password", headers=h,
                     json={"old_password": "wh1234", "new_password": "newpass1"}).status_code == 204

    # Idevhgui bolgovol nevtrehgui
    ok(c.patch(f"/api/auth/users/{u['id']}", json={"is_active": False}))
    assert anon.post("/api/auth/login", json={"username": "wh1", "password": "newpass1"}).status_code == 401

    # Admin uuriigee tugjihgui, dur/modulin husnegt
    admin_id = ok(c.get("/api/auth/me"))["id"]
    assert c.patch(f"/api/auth/users/{admin_id}", json={"is_active": False}).status_code == 409
    assert c.patch(f"/api/auth/users/{admin_id}", json={"role": "driver"}).status_code == 409
    roles = {r["role"]: r["modules"] for r in ok(c.get("/api/auth/roles"))}
    assert roles["accountant"] == ["orders", "finance", "notifications"]
    assert len(roles["admin"]) == 6


def test_login_pages(c):
    anon = TestClient(app)
    for path in ("/login", "/login/warehouse", "/login/orders"):
        r = anon.get(path)
        assert r.status_code == 200 and "login.js" in r.text
    r = anon.get("/login/unknown", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/login"


def test_login_lockout_and_audit(c):
    from modules.auth.backend import service as auth_service
    anon = TestClient(app)
    ok(c.post("/api/auth/users", json={"username": "lock1", "password": "lock123", "role": "driver"}), 201)
    for left in (4, 3, 2, 1, 0):
        r = anon.post("/api/auth/login", json={"username": "lock1", "password": "bad"})
        assert r.status_code == 401 and r.json()["error"]["attempts_left"] == left
    r = anon.post("/api/auth/login", json={"username": "lock1", "password": "lock123"})
    assert r.status_code == 429 and r.json()["error"]["retry_minutes"] >= 1
    auth_service._fails.clear()  # tugjeeg tailbal zuv nuuts ug ajillana
    assert anon.post("/api/auth/login", json={"username": "lock1", "password": "lock123"}).status_code == 200

    log = ok(c.get("/api/auth/audit", params={"entity": "auth", "size": 50}))
    assert log["total"] > 0 and all(i["entity"].startswith("auth") for i in log["items"])
    assert any(i["action"] == "login" and i["user_name"] for i in log["items"])
    tok = anon.post("/api/auth/login", json={"username": "lock1", "password": "lock123"}).json()["access_token"]
    assert anon.get("/api/auth/audit", headers={"Authorization": f"Bearer {tok}"}).status_code == 403


def test_finance_report_export(c):
    from io import BytesIO
    from urllib.parse import unquote

    from openpyxl import load_workbook

    r = c.get("/api/finance/reports/export")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    cd = r.headers["content-disposition"]
    assert "attachment" in cd and "Санхүүгийн_тайлан_" in unquote(cd)
    wb = load_workbook(BytesIO(r.content))
    assert wb.sheetnames == ["Тойм", "Сарын урсгал", "Авлагын насжилт", "Зардал ангиллаар",
                             "Авлагатай харилцагч", "Нэхэмжлэх", "Төлбөр", "Зардал"]
    summary = ok(c.get("/api/finance/reports/summary"))
    kpi = {wb["Тойм"].cell(row=i, column=1).value: wb["Тойм"].cell(row=i, column=2).value for i in range(6, 12)}
    assert kpi["Нийт авлага (өнөөдрийн байдлаар)"] == summary["totals"]["outstanding"]
    assert len(wb["Сарын урсгал"]._charts) == 1
    inv = wb["Нэхэмжлэх"]
    numbers = [inv.cell(row=i, column=1).value for i in range(5, inv.max_row + 1)]
    assert any(str(n).startswith("INV-") for n in numbers) and inv.cell(row=inv.max_row, column=6).value.startswith("=SUM(")
    assert c.get("/api/finance/reports/export", params={"date_from": "2026-12-01", "date_to": "2026-01-01"}).status_code == 422

    # finance:read erhgui (agualah) tatah bolomjgui
    anon = TestClient(app)
    ok(c.post("/api/auth/users", json={"username": "whx", "password": "whx123", "role": "warehouse"}), 201)
    tok = anon.post("/api/auth/login", json={"username": "whx", "password": "whx123"}).json()["access_token"]
    assert anon.get("/api/finance/reports/export", headers={"Authorization": f"Bearer {tok}"}).status_code == 403


def test_finance_export_link(c):
    from urllib.parse import parse_qs, urlparse
    anon = TestClient(app)
    link = ok(c.post("/api/finance/reports/export-link", params={"date_from": "2026-01-01", "date_to": "2026-06-30"}))
    assert link["url"].startswith("/api/finance/reports/export?") and link["expires_in"] == 120
    # Brauzer shig: Authorization header-gui, zuvhun link-eer
    r = anon.get(link["url"])
    assert r.status_code == 200 and r.content[:2] == b"PK"  # xlsx (zip)
    assert "2026-01-01_2026-06-30" in r.headers["content-disposition"]
    dl = parse_qs(urlparse(link["url"]).query)["dl"][0]
    # Tatah token-oor busad API-d nevtrehgui
    assert anon.get("/api/finance/invoices", headers={"Authorization": f"Bearer {dl}"}).status_code == 401
    assert anon.get("/api/finance/reports/export", params={"dl": "garbage"}).status_code == 401
    assert anon.get("/api/finance/reports/export").status_code == 401
    # Huuchin JS kesh-lehgui
    assert anon.get("/erp-ui").headers.get("cache-control") == "no-cache"
    assert anon.get("/erp_frontend/static/src/js/finance.js").headers.get("cache-control") == "no-cache"


def test_login_as_admin_or_user(c):
    anon = TestClient(app)
    ok(c.post("/api/auth/users", json={"username": "disp9", "password": "disp123", "role": "dispatcher"}), 201)

    def login(u, p, **kw):
        return anon.post("/api/auth/login", json={"username": u, "password": p, **kw})

    # Admin songolt: zuvhun admin
    assert login("admin", "admin12345", login_as="admin").status_code == 200
    r = login("disp9", "disp123", login_as="admin", module="transport")
    assert r.status_code == 403 and r.json()["error"]["reason"] == "not_admin"
    # Ajiltan songolt: admin bish
    assert login("disp9", "disp123", login_as="user", module="transport").status_code == 200
    r = login("admin", "admin12345", login_as="user", module="finance")
    assert r.status_code == 403 and r.json()["error"]["reason"] == "use_admin"
    # Songoltgui (API/Swagger) huuchin yostoi
    assert login("admin", "admin12345").status_code == 200
    assert anon.get("/login/admin").status_code == 200


def test_self_registration(c):
    from modules.auth.backend import service as auth_service
    auth_service._regs.clear()
    anon = TestClient(app)
    r = anon.post("/api/auth/register", json={"username": "new.user", "full_name": "Шинэ Хэрэглэгч",
                                              "password": "secret1", "role": "accountant"})
    assert r.status_code == 201 and r.json()["pending"] is True
    # Admin-aar burtguulehgui, davhtsal, buruu ner
    assert anon.post("/api/auth/register", json={"username": "x.admin", "full_name": "XX", "password": "secret1",
                                                 "role": "admin"}).status_code == 422
    assert anon.post("/api/auth/register", json={"username": "new.user", "full_name": "Dup", "password": "secret1"}).status_code == 409
    assert anon.post("/api/auth/register", json={"username": "bad name!", "full_name": "XX", "password": "secret1"}).status_code == 422
    # Batlagdahaas umnu nevtrehgui
    r = anon.post("/api/auth/login", json={"username": "new.user", "password": "secret1", "login_as": "user"})
    assert r.status_code == 401 and r.json()["error"]["reason"] == "pending"
    # Admin-d medegdel, huselt jagsaaltad
    assert "user.registered" in {n["event"] for n in ok(c.get("/api/notifications", params={"size": 100}))["items"]}
    pend = [u for u in ok(c.get("/api/auth/users")) if u["pending"]]
    assert [u["username"] for u in pend] == ["new.user"] and pend[0]["role"] == "accountant"
    # Batlah (uureg uurchilj)
    u = ok(c.post(f"/api/auth/users/{pend[0]['id']}/approve", json={"role": "warehouse"}))
    assert u["is_active"] and not u["pending"] and u["role"] == "warehouse"
    r = anon.post("/api/auth/login", json={"username": "new.user", "password": "secret1", "login_as": "user",
                                           "module": "warehouse"})
    assert r.status_code == 200
    assert c.post(f"/api/auth/users/{u['id']}/reject").status_code == 409  # batlagdsan bol tatgalzahgui
    # Tatgalzah = ustgana
    rid = anon.post("/api/auth/register", json={"username": "rej.user", "full_name": "Татгалзах", "password": "secret1"}).json()["id"]
    assert c.post(f"/api/auth/users/{rid}/reject").status_code == 204
    assert all(x["username"] != "rej.user" for x in ok(c.get("/api/auth/users")))
    # Spam hamgaalalt
    auth_service._regs.clear()
    codes = [anon.post("/api/auth/register", json={"username": f"spam{i}", "full_name": "Spam", "password": "secret1"}).status_code
             for i in range(6)]
    assert codes[:5] == [201] * 5 and codes[5] == 429
    assert anon.get("/register").status_code == 200


def test_plain_user_role(c):
    from modules.auth.backend import service as auth_service
    auth_service._regs.clear()
    anon = TestClient(app)
    r = anon.post("/api/auth/register", json={"username": "plain1", "full_name": "Энгийн Хэрэглэгч", "password": "plain123"})
    assert r.status_code == 201
    uid = r.json()["id"]
    assert [u for u in ok(c.get("/api/auth/users")) if u["id"] == uid][0]["role"] == "user"  # anhdagch
    ok(c.post(f"/api/auth/users/{uid}/approve", json={}))
    tok = anon.post("/api/auth/login", json={"username": "plain1", "password": "plain123", "login_as": "user"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    me = ok(anon.get("/api/auth/me", headers=h))
    assert me["role"] == "user" and me["modules"] == ["notifications"]
    # Busad modulin medeelel haragdahgui
    for path in ("/api/transport/trips", "/api/transport/vehicles", "/api/orders", "/api/warehouse/stock",
                 "/api/finance/invoices", "/api/masterdata/customers", "/api/routing/trips/1", "/api/auth/users"):
        assert anon.get(path, headers=h).status_code == 403, path
    r = anon.post("/api/auth/login", json={"username": "plain1", "password": "plain123", "login_as": "user", "module": "transport"})
    assert r.status_code == 403
    # Uuriin medeelel
    assert ok(anon.get("/api/notifications/unread-count", headers=h))["count"] >= 0
    assert ok(anon.patch("/api/auth/me", headers=h, json={"full_name": "Шинэ Нэр"}))["full_name"] == "Шинэ Нэр"
    acts = ok(anon.get("/api/auth/me/activity", headers=h))
    assert {"login", "update"} <= {a["action"] for a in acts} and all(a["user_id"] == uid for a in acts)


def test_customer_portal_order_and_tracking(c):
    from modules.auth.backend import service as auth_service
    auth_service._regs.clear()
    anon = TestClient(app)
    uid = anon.post("/api/auth/register", json={"username": "cust1", "full_name": "Харилцагч Нэг", "password": "cust123"}).json()["id"]
    ok(c.post(f"/api/auth/users/{uid}/approve", json={}))
    tok = anon.post("/api/auth/login", json={"username": "cust1", "password": "cust123", "login_as": "user"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    me = ok(anon.get("/api/portal/me", headers=h))
    assert me["customer_name"] == "Харилцагч Нэг" and me["customer_code"] == f"U-{uid}"

    # Baraa (agualahad uldegdeltei), hayag
    md = "/api/masterdata"
    wh = ok(c.post(f"{md}/locations", json={"name": "Portal WH", "type": "warehouse", "lat": 47.9, "lng": 106.9}), 201)
    prod = ok(c.post(f"{md}/products", json={"sku": "PORT-1", "name": "Портал бараа", "price": "2500", "weight_kg": 2}), 201)
    ok(c.post("/api/warehouse/movements", json={"location_id": wh["id"], "product_id": prod["id"], "type": "in", "quantity": "100"}), 201)
    assert any(p["sku"] == "PORT-1" for p in ok(anon.get("/api/portal/products", headers=h)))
    addr = ok(anon.post("/api/portal/addresses", headers=h, json={"name": "Гэр", "address": "БЗД, 13-р хороо", "lat": 47.92, "lng": 106.95}), 201)

    # Zahialga ugnu: une = baraanii une
    o = ok(anon.post("/api/portal/orders", headers=h, json={"delivery_location_id": addr["id"], "notes": "Өглөө",
                                                            "lines": [{"product_id": prod["id"], "quantity": "4"}]}), 201)
    assert o["status"] == "draft" and o["total_amount"] == 10000 and o["delivery_location"]["name"] == "Гэр"
    assert "order.submitted" in {n["event"] for n in ok(c.get("/api/notifications", params={"size": 200}))["items"]}

    # Busdiin hayag, busdiin zahialga -> 404; ajiltnii API -> 403
    other = ok(c.post(f"{md}/locations", json={"name": "Бусдын", "type": "customer"}), 201)
    assert anon.post("/api/portal/orders", headers=h, json={"delivery_location_id": other["id"],
                                                            "lines": [{"product_id": prod["id"], "quantity": "1"}]}).status_code == 404
    cust_other = ok(c.post(f"{md}/customers", json={"name": "Өөр компани"}), 201)
    foreign = ok(c.post("/api/orders", json={"customer_id": cust_other["id"], "lines": [{"product_id": prod["id"], "quantity": "1"}]}), 201)
    assert anon.get(f"/api/portal/orders/{foreign['id']}", headers=h).status_code == 404
    assert all(x["id"] != foreign["id"] for x in ok(anon.get("/api/portal/orders", headers=h)))
    assert anon.get(f"/api/orders/{o['id']}", headers=h).status_code == 403

    # Dispetcher: batlah -> beltgeh -> ilgeeh -> aylal
    for to in ("confirmed", "picking", "shipped"):
        ok(c.post(f"/api/orders/{o['id']}/status", json={"to": to}))
    sh = [s for s in ok(c.get("/api/transport/shipments"))["items"] if s["order_id"] == o["id"]][0]
    v = ok(c.post("/api/transport/vehicles", json={"plate_no": "PORT 01"}), 201)
    d = ok(c.post("/api/transport/drivers", json={"full_name": "Portal Driver", "phone": "99009900"}), 201)
    trip = ok(c.post("/api/transport/trips", json={"vehicle_id": v["id"], "driver_id": d["id"], "planned_date": "2026-11-06",
                                                  "depot_location_id": wh["id"], "shipment_ids": [sh["id"]]}), 201)
    ok(c.post(f"/api/transport/trips/{trip['id']}/start"))
    t = ok(anon.get(f"/api/portal/orders/{o['id']}", headers=h))
    assert t["status"] == "shipped" and t["shipment"]["status"] == "in_transit"
    assert t["trip"]["vehicle_plate"] == "PORT 01" and t["trip"]["driver_phone"] == "99009900"
    assert t["trip"]["my_stop"] == 1 and t["trip"]["stops_total"] == 1
    mine = {n["event"] for n in ok(anon.get("/api/notifications", headers=h, params={"size": 50}))["items"]}
    assert {"order.confirmed", "order.shipped", "trip.started"} <= mine

    ok(c.post(f"/api/transport/shipments/{sh['id']}/deliver"))
    t = ok(anon.get(f"/api/portal/orders/{o['id']}", headers=h))
    assert t["status"] == "delivered" and t["invoice"]["amount"] == 10000 and t["trip"]["driver_phone"] is None
    assert "order.delivered" in {n["event"] for n in ok(anon.get("/api/notifications", headers=h, params={"size": 50}))["items"]}

    # Draft-iig uuruu tsutsalna, batlagdsaniig chadahgui
    o2 = ok(anon.post("/api/portal/orders", headers=h, json={"lines": [{"product_id": prod["id"], "quantity": "1"}]}), 201)
    assert ok(anon.post(f"/api/portal/orders/{o2['id']}/cancel", headers=h))["status"] == "cancelled"
    assert anon.post(f"/api/portal/orders/{o['id']}/cancel", headers=h).status_code == 409
