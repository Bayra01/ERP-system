# Logistics ERP

FastAPI + SQLAlchemy 2 + Alembic. Modul burt neg gishuun hariutsana.

## Ehluulleh
```bash
pip install -r requirements.txt
<<<<<<< HEAD
cp -n .env.example .env              # .env байхгүй үед л (байгаа .env-ийг дарж бичихгүй)
alembic upgrade head               # PostgreSQL bol (sqlite deer avtomataar uusne)
python seed.py                     # (songoltoor) demo aguulah/baraa/mashin/hereglegch
python seed_finance.py             # (songoltoor) sanhuugiin 12 sariin jishee ugugdul (--clear ustgana)
uvicorn main:app --reload
pytest
```
Dev (sqlite) deer table avtomataar uusne, anhnii admin: `admin / admin12345`.
`seed.py` hereglegchid: `dispatcher`, `warehouse`, `driver`, `accountant` (nuuts ug = `<ner>123`).

| URL | Yu |
|---|---|
| http://localhost:8000/login | Modul songoh -> `/login/<modul>` (orders, warehouse, transport, routing, finance, notifications) |
| http://localhost:8000/erp-ui | Aguulah ba Teever UI (`erp_frontend/`) |
| http://localhost:8000/orders/ | Zahialgiin UI (React build: `cd modules/orders/frontend && npm install && npm run build`) |
| http://localhost:5174 | Zahialgiin UI dev (`npm run dev`, /api -> :8000 proxy) |
| http://localhost:8000/docs | Swagger (Authorize -> login-oos avsan access_token) |

Bukh UI neg origin deer bol `localStorage["erp-token"]`-g huvaaltsana (neg udaa nevtrene).
Dev server-uudad CORS: `.env` -> `CORS_ORIGINS`.
=======
cp .env.example .env
uvicorn main:app --reload          # http://localhost:8000/docs
pytest
```
Dev (sqlite) deer table avtomataar uusne, anhnii admin: `admin / admin12345`.
Prod (PostgreSQL): `alembic upgrade head`.
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4

## Gishuun burt (modul-iin ezen) yaaj ajillah ve
1. `modules/<modul>/backend/models.py` - `from core.database import Base`, `IdMixin, TimestampMixin` ashiglana. Table ner: `<ugtvar>_xxx` (orders_, wh_, tr_, fin_, routing_, notif_).
2. Model uurchlugdsunii daraa: `alembic revision --autogenerate -m "orders: add order tables"` -> `alembic upgrade head`.
3. Router deer erh: `dependencies=[Depends(require_permission("orders:write"))]` (`core/deps.py`). Shine permission bol `core/permissions.py`-d nemne.
4. Aldaa: `raise NotFoundError("...")` (`core/exceptions.py`). Jagsaalt: `PageParams` + `paginate` (`core/pagination.py`).
5. Busad modultei: shuud import hiihgui, `core/events.py`-eer. Jishee: `events.publish("order.confirmed", {"order_id": 1})`.
6. Uurchlult tus bur: `core/audit.py` -> `log_action(...)`.
7. Router-iin prefix `/api/<modul>` modul dotroo tohirogdono; main.py-d nemehgui.

## Modulud
| Modul | Prefix | Tuluv |
|---|---|---|
| auth | /api/auth | duussan |
| masterdata (Customers, Products, Locations) | /api/masterdata | duussan |
| orders (Order, OrderLine, status machine) | /api/orders | duussan |
| warehouse (stock, movement, reservation) | /api/warehouse | duussan |
| transport (Vehicle, Driver, Shipment, Trip) | /api/transport | duussan |
| finance (Invoice, Payment, Expense) | /api/finance | duussan |
<<<<<<< HEAD
| routing (nearest-neighbour marshrut, haversine zai) | /api/routing | duussan |
| notifications (event -> role-oor hereglegch burt) | /api/notifications | duussan |
=======
| routing, notifications | /api/<modul> | gishuun burt |
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4

Master data: orders/warehouse/transport ene table-uudiin `id`-g FK-eer holbono
(`md_customers.id`, `md_products.id`, `md_locations.id`). Ustgal bol soft delete (`deleted_at`).

## Orders: status machine ba event
`draft -> confirmed -> picking -> shipped -> delivered`, `cancelled` (draft/confirmed/picking-oos).
Status burt `core.events` deer `order.<status>` event garna
(payload: order_id, order_no, customer_id, from_status, delivery_location_id, lines, total_amount).

- Warehouse: `order.confirmed` -> stock reserve, `order.cancelled` -> release, `order.shipped` -> stock hasah
- Transport/Routing: `order.picking`/`order.shipped` -> hurgeltiin delivery uusgeh
- Finance: `order.delivered` -> invoice uusgeh
- Notifications: bukh `order.*`

Status shiljiltiin erh: confirmed/cancelled=`orders:write`, picking/shipped=`orders:fulfil`, delivered=`orders:deliver`.

## Warehouse
Aguulah = `md_locations` (type=`warehouse`). Stock = `wh_stock` (on_hand, reserved, available=on_hand-reserved),
ledger = `wh_movements` (in/out/adjust/transfer_in/transfer_out), zahialgiin reserve = `wh_reservations`.

Sonsdog: `order.confirmed` (reserve, hureehgui bol `short`), `order.cancelled` (release), `order.shipped` (stock-oos hasna).
Gargadag: `stock.shortage` {order_id, shortages, stage} -> Notifications sonsoj bolno.
Uldegdel nemegdsenii daraa: `POST /api/warehouse/orders/{id}/reserve` (short reserve-g dahin hiine).

Test deer `events.clear()`-iin orond `events.snapshot()` / `events.restore()` ashigla (busad modulin handler-g ustgahgui).

## Transport
`tr_vehicles`, `tr_drivers` (user_id -> jolooch role-toi hereglegch), `tr_shipments` (zahialga burt 1 zogsoltsoo), `tr_trips`.

Sonsdog: `order.picking` (shipment uusgene, jin/omnoh baraanaas), `order.shipped` (ready=True), `order.cancelled` (shipment cancelled).
Gargadag: `trip.started`, `shipment.delivered`, `shipment.failed`, `trip.completed`.
Orders `shipment.delivered`-g sonsoj zahialgiig `delivered` bolgono (-> Finance invoice uusgeh).

Trip: planned -> in_progress -> completed (suuliin zogsolt shiidegdehed avtomataar). Planned deer cancel hiij bolno.
Trip ehluuleh nuhtsul: buh shipment `ready` (order 'shipped'). Achaa mashinii capacity-s hetreh bolomjgui.
Jolooch (role=driver) zuvhun uuriin trip deer deliver/fail hiine, `GET /api/transport/my/trips`.
Routing modul daraa n `Trip.stops` (stop_sequence) ba `total_distance_km`-g bugluj ugnu.

## Finance
`fin_invoices` (nehemjleh, `paid` = tulburuuden niilber), `fin_payments`, `fin_expenses`.
Endpoint: `GET/POST /api/finance/{invoices,payments,expenses}`, `GET /api/finance/invoices/{id}`.
<<<<<<< HEAD
Tailan: `GET /api/finance/reports/summary` (JSON), `GET /api/finance/reports/export?date_from=&date_to=` (Excel .xlsx, 8 sheet; `modules/finance/backend/export.py`).
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
List endpoint Page biš, **Array** butsaana (frontend ene shapeeer ajilladag). Dun = number, talbaruud camelCase (`invoiceId`).
Erh: `finance:read` / `finance:write` (admin, accountant).

Sonsdog: `order.delivered` -> nehemjleh uusgene (dun = order.total_amount, tulukh hugatsaa +30 honog, 1 zahialga = 1 nehemjleh).
Tulbur: nehemjlehiin uldegdelees ih baij bolohgui, buten tulugdsun nehemjleh deer 409.
Nehemjleh gar aaraa uusgehed `customer` (ner) ugsun ch bolno: oldohgui bol shine kharitsagch (`AUTO-<id>`) uusgene, esvel `customer_id` ugnu.
<<<<<<< HEAD

## Routing
`POST /api/routing/trips/{id}/optimize` - planned aylliin zogsoltuudyg aguulahaas (depot) ehlen hamgiin oir daraallaar
erembeleh (`Shipment.stop_sequence`), `Trip.total_distance_km`-g bugluno. Bairshild lat/lng baihgui zogsolt tugsgold orno.
`GET /api/routing/trips/{id}` - zogsolt burt leg_km. `GET /api/routing/distance?from_id=&to_id=`.

## Notifications
`notif_notifications` (hereglegch burt mor). `order.*`, `stock.shortage`, `shipment.failed`, `trip.*` event garahad
zohih role-tei (ba admin) idevhtei hereglegch burt uusne.
`GET /api/notifications?unread=true`, `GET /api/notifications/unread-count`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all`.

## Shine endpoint-uud (UI-d zoriulsan)
- `PUT /api/routing/trips/{id}/sequence` `{shipment_ids}` - garaar daraalal. optimize/sequence hariu `previous_km` aguulna.
- `GET /api/finance/reports/summary?date_from=&date_to=` - totals, monthly, aging, expensesByCategory, topDebtors (default: suuliin 6 sar).
- `POST /api/notifications/send` `{to_user_id | role | reply_to, title, message}`, `GET /api/notifications/recipients`,
  `GET /api/notifications?box=sent|inbox&kind=message|system`. Migration `0008` (`sender_id`).

## Nevtrelt (modul burt)
`/login/<modul>` huudas `POST /api/auth/login {username, password, module}` duudna. Tuhain role-d modul
(`core/permissions.py: MODULE_PERMISSIONS`) baihgui bol 403 `{"error": {"code": "forbidden", "allowed": [...], "role": ...}}`.
Nevtersnii daraa shuud modul ruu (`?next=` baival tend). `/api/auth/me` -> `modules` (nevterch boloh modul).
Ajiltnuud: admin `/erp-ui#us` (`GET/POST /api/auth/users`, `PATCH /api/auth/users/{id}`, `GET /api/auth/roles`);
admin uuriigee bolon suuliin adminiig idevhgui/dur buuruulah bolomjgui. Ajiltan burt "Nuuts ug" -> `POST /api/auth/me/password`.
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
