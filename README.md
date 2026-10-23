# Logistics ERP

FastAPI + SQLAlchemy 2 + Alembic. Modul burt neg gishuun hariutsana.

## Ehluulleh
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload          # http://localhost:8000/docs
pytest
```
Dev (sqlite) deer table avtomataar uusne, anhnii admin: `admin / admin12345`.
Prod (PostgreSQL): `alembic upgrade head`.

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
| routing, finance, notifications | /api/<modul> | gishuun burt |

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
