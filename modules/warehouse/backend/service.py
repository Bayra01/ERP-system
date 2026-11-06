<<<<<<< HEAD
"""Uldegdel, hudulguun, zahialgiin reserve."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from core import events
from core.exceptions import ConflictError, UnprocessableError
from modules.masterdata.backend.models import Location, Product

from .models import Movement, Reservation, Stock

ZERO = Decimal(0)


def check_warehouse(db: Session, location_id: int) -> Location:
    loc = db.get(Location, location_id)
    if loc is None or loc.deleted_at is not None or loc.type != "warehouse":
        raise UnprocessableError(f"Aguulah #{location_id} oldsongui (type=warehouse baih yostoi)")
    return loc


def check_product(db: Session, product_id: int) -> Product:
    p = db.get(Product, product_id)
    if p is None or p.deleted_at is not None:
        raise UnprocessableError(f"Baraa #{product_id} oldsongui")
    return p


def get_stock(db: Session, location_id: int, product_id: int) -> Stock:
    st = db.scalar(select(Stock).where(Stock.location_id == location_id,
                                       Stock.product_id == product_id))
    if st is None:
        st = Stock(location_id=location_id, product_id=product_id, on_hand=ZERO, reserved=ZERO,
                   min_level=ZERO)
=======
"""Warehouse: stock, movement ledger, reservation. Orders-iin event-uudiig sonsono.

Sonsdog event:
  order.confirmed -> uldegdel reserve (hureehgui bol 'short' + stock.shortage event)
  order.cancelled -> reserve chuluulnu
  order.shipped   -> reserve-g stock-oos hasna (movement 'out'), reserve = consumed
Gargadag event:
  stock.shortage  {order_id, shortages:[{product_id, quantity}], stage}
"""
import logging
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core import events
from core.audit import log_action
from core.database import SessionLocal
from core.exceptions import ConflictError, NotFoundError, UnprocessableError
from core.pagination import PageParams, paginate
from modules.masterdata.backend.models import Location, Product

from .models import Movement, Reservation, Stock
from .schemas import AdjustIn, IssueIn, ReceiptIn, TransferIn

log = logging.getLogger("erp.warehouse")
ZERO = Decimal("0")


# ---------------- helpers
def _check_warehouse(db: Session, location_id: int) -> Location:
    loc = db.get(Location, location_id)
    if loc is None or loc.deleted_at is not None or not loc.is_active:
        raise UnprocessableError(f"Aguulah oldsongui: id={location_id}")
    if loc.type != "warehouse":
        raise UnprocessableError(f"Ene hayag aguulah bish (type={loc.type}): id={location_id}")
    return loc


def _check_product(db: Session, product_id: int) -> None:
    p = db.get(Product, product_id)
    if p is None or p.deleted_at is not None or not p.is_active:
        raise UnprocessableError(f"Baraa oldsongui esvel idevhgui: id={product_id}")


def _stock(db: Session, location_id: int, product_id: int) -> Stock:
    st = db.scalar(select(Stock).where(Stock.location_id == location_id, Stock.product_id == product_id))
    if st is None:
        st = Stock(location_id=location_id, product_id=product_id, on_hand=ZERO, reserved=ZERO, min_level=ZERO)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
        db.add(st)
        db.flush()
    return st


<<<<<<< HEAD
def _ledger(db: Session, st: Stock, type_: str, delta: Decimal, user_id: int | None,
            ref_type: str | None = None, ref_id: int | None = None,
            note: str | None = None) -> Movement:
    st.on_hand = Decimal(st.on_hand) + delta
    mv = Movement(location_id=st.location_id, product_id=st.product_id, type=type_, quantity=delta,
                  balance_after=st.on_hand, ref_type=ref_type, ref_id=ref_id, note=note,
                  user_id=user_id)
=======
def apply_movement(db: Session, *, location_id: int, product_id: int, mtype: str, delta: Decimal,
                   user_id: int | None = None, note: str | None = None, ref_type: str | None = None,
                   ref_id: int | None = None, from_reserved: Decimal = ZERO) -> Movement:
    """on_hand-g delta-aar uurchilnu. Commit hiihgui (duudagch commit hiine).
    Zahialgand zuugdsun (reserved) uldegdliig dahin hasaj bolohgui."""
    st = _stock(db, location_id, product_id)
    st.reserved = st.reserved - from_reserved
    new_on_hand = st.on_hand + delta
    if new_on_hand < st.reserved:
        raise ConflictError(
            f"Uldegdel hureltsehgui: on_hand={st.on_hand}, reserved={st.reserved}, huselt={delta}")
    st.on_hand = new_on_hand
    mv = Movement(location_id=location_id, product_id=product_id, type=mtype, quantity=delta,
                  balance_after=new_on_hand, ref_type=ref_type, ref_id=ref_id, note=note, user_id=user_id)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    db.add(mv)
    return mv


<<<<<<< HEAD
def move(db: Session, location_id: int, product_id: int, type_: str, quantity: Decimal,
         user_id: int | None, note: str | None = None) -> Movement:
    """type_: in (+qty), out (-qty, available-aas), adjust (on_hand = qty, toollogo)."""
    check_warehouse(db, location_id)
    check_product(db, product_id)
    st = get_stock(db, location_id, product_id)
    if type_ == "in":
        delta = quantity
    elif type_ == "out":
        if quantity > st.available:
            raise ConflictError(f"Uldegdel hureltsehgui (bolomjit: {st.available.normalize()})")
        delta = -quantity
    else:  # adjust
        if quantity < Decimal(st.reserved):
            raise ConflictError("Toollogiin too reserve-ees baga baij bolohgui")
        delta = quantity - Decimal(st.on_hand)
    mv = _ledger(db, st, type_, delta, user_id, note=note)
    db.commit()
    return mv


def transfer(db: Session, src: int, dst: int, product_id: int, quantity: Decimal,
             user_id: int | None, note: str | None = None) -> None:
    if src == dst:
        raise UnprocessableError("Ijil aguulah ruu shiljuulehgui")
    check_warehouse(db, src)
    check_warehouse(db, dst)
    check_product(db, product_id)
    s, d = get_stock(db, src, product_id), get_stock(db, dst, product_id)
    if quantity > s.available:
        raise ConflictError(f"Uldegdel hureltsehgui (bolomjit: {s.available.normalize()})")
    _ledger(db, s, "transfer_out", -quantity, user_id, "transfer", dst, note)
    _ledger(db, d, "transfer_in", quantity, user_id, "transfer", src, note)
    db.commit()


# ---------------- Zahialgiin reserve
def _pick_location(db: Session, product_id: int, qty: Decimal) -> Stock | None:
    """Hamgiin ih bolomjit uldegdeltei aguulah (qty-g buren hangah)."""
    rows = db.scalars(select(Stock).join(Location, Location.id == Stock.location_id)
                      .where(Stock.product_id == product_id, Location.type == "warehouse",
                             Location.deleted_at.is_(None))).all()
    rows = [r for r in rows if r.available >= qty]
    return max(rows, key=lambda r: r.available, default=None)


def _try_reserve(db: Session, r: Reservation) -> bool:
    st = _pick_location(db, r.product_id, Decimal(r.quantity))
    if st is None:
        r.status, r.location_id = "short", None
        return False
    st.reserved = Decimal(st.reserved) + Decimal(r.quantity)
    r.status, r.location_id = "reserved", st.location_id
    return True


def _shortages(rows: list[Reservation]) -> list[dict]:
    return [{"product_id": r.product_id, "quantity": float(r.quantity)}
            for r in rows if r.status == "short"]


def reserve_order(db: Session, order_id: int, lines: list[dict]) -> list[Reservation]:
    active = db.scalars(select(Reservation).where(
        Reservation.order_id == order_id, Reservation.status.in_(("reserved", "short")))).all()
    if active:  # davhar reserve hiihgui
        return list(active)
    rows = []
    for ln in lines:
        r = Reservation(order_id=order_id, product_id=ln["product_id"],
                        quantity=Decimal(str(ln["quantity"])))
        db.add(r)
        _try_reserve(db, r)
        rows.append(r)
    db.commit()
    if short := _shortages(rows):
        events.publish("stock.shortage", {"order_id": order_id, "shortages": short,
                                          "stage": "confirmed"})
    return rows


def retry_short(db: Session, order_id: int) -> list[Reservation]:
    rows = db.scalars(select(Reservation).where(Reservation.order_id == order_id,
                                                Reservation.status.in_(("reserved", "short")))).all()
    for r in rows:
        if r.status == "short":
            _try_reserve(db, r)
    db.commit()
    return list(rows)


def release_order(db: Session, order_id: int) -> None:
    rows = db.scalars(select(Reservation).where(Reservation.order_id == order_id,
                                                Reservation.status.in_(("reserved", "short")))).all()
    for r in rows:
        if r.status == "reserved" and r.location_id is not None:
            st = get_stock(db, r.location_id, r.product_id)
            st.reserved = max(ZERO, Decimal(st.reserved) - Decimal(r.quantity))
        r.status = "released"
    db.commit()


def consume_order(db: Session, order_id: int, lines: list[dict]) -> None:
    """Ilgeesen: reserve-g on_hand-aas hasna. Reserve baihgui bol odoo reserve hiij uzne."""
    rows = db.scalars(select(Reservation).where(Reservation.order_id == order_id,
                                                Reservation.status.in_(("reserved", "short")))).all()
    if not rows:
        rows = reserve_order(db, order_id, lines)
    for r in rows:
        if r.status == "short":
            _try_reserve(db, r)
        if r.status != "reserved":
            continue
        st = get_stock(db, r.location_id, r.product_id)
        st.reserved = max(ZERO, Decimal(st.reserved) - Decimal(r.quantity))
        _ledger(db, st, "out", -Decimal(r.quantity), None, "order", order_id, "Zahialga ilgeesen")
        r.status = "consumed"
    db.commit()
    if short := _shortages(rows):
        events.publish("stock.shortage", {"order_id": order_id, "shortages": short,
                                          "stage": "shipped"})
=======
# ---------------- manual operations
def receive(db: Session, data: ReceiptIn, user_id: int | None) -> Movement:
    _check_warehouse(db, data.location_id)
    _check_product(db, data.product_id)
    mv = apply_movement(db, location_id=data.location_id, product_id=data.product_id, mtype="in",
                        delta=data.quantity, user_id=user_id, note=data.note)
    db.commit()
    log_action(db, user_id, "receipt", "warehouse.Stock", data.product_id, {"qty": str(data.quantity)})
    return mv


def issue(db: Session, data: IssueIn, user_id: int | None) -> Movement:
    _check_warehouse(db, data.location_id)
    _check_product(db, data.product_id)
    mv = apply_movement(db, location_id=data.location_id, product_id=data.product_id, mtype="out",
                        delta=-data.quantity, user_id=user_id, note=data.note)
    db.commit()
    log_action(db, user_id, "issue", "warehouse.Stock", data.product_id, {"qty": str(data.quantity)})
    return mv


def adjust(db: Session, data: AdjustIn, user_id: int | None) -> Movement:
    _check_warehouse(db, data.location_id)
    _check_product(db, data.product_id)
    mv = apply_movement(db, location_id=data.location_id, product_id=data.product_id, mtype="adjust",
                        delta=data.quantity, user_id=user_id, note=data.note)
    db.commit()
    log_action(db, user_id, "adjust", "warehouse.Stock", data.product_id, {"qty": str(data.quantity)})
    return mv


def transfer(db: Session, data: TransferIn, user_id: int | None) -> list[Movement]:
    if data.from_location_id == data.to_location_id:
        raise UnprocessableError("Ilgeegch, hulleen avagch aguulah neg bairtai baij bolohgui")
    _check_warehouse(db, data.from_location_id)
    _check_warehouse(db, data.to_location_id)
    _check_product(db, data.product_id)
    out = apply_movement(db, location_id=data.from_location_id, product_id=data.product_id,
                         mtype="transfer_out", delta=-data.quantity, user_id=user_id, note=data.note)
    inn = apply_movement(db, location_id=data.to_location_id, product_id=data.product_id,
                         mtype="transfer_in", delta=data.quantity, user_id=user_id, note=data.note)
    db.commit()
    log_action(db, user_id, "transfer", "warehouse.Stock", data.product_id, {"qty": str(data.quantity)})
    return [out, inn]


def set_min_level(db: Session, stock_id: int, min_level: Decimal, user_id: int | None) -> Stock:
    st = db.get(Stock, stock_id)
    if st is None:
        raise NotFoundError("Stock oldsongui")
    st.min_level = min_level
    db.commit()
    log_action(db, user_id, "update", "warehouse.Stock", stock_id, {"min_level": str(min_level)})
    return st


# ---------------- queries
def list_stock(db: Session, params: PageParams, location_id=None, product_id=None, low_only=False):
    stmt = select(Stock)
    if location_id is not None:
        stmt = stmt.where(Stock.location_id == location_id)
    if product_id is not None:
        stmt = stmt.where(Stock.product_id == product_id)
    if low_only:
        stmt = stmt.where(Stock.on_hand - Stock.reserved <= Stock.min_level)
    return paginate(db, stmt.order_by(Stock.id), params)


def list_movements(db: Session, params: PageParams, location_id=None, product_id=None,
                   mtype=None, ref_type=None, ref_id=None):
    stmt = select(Movement)
    if location_id is not None:
        stmt = stmt.where(Movement.location_id == location_id)
    if product_id is not None:
        stmt = stmt.where(Movement.product_id == product_id)
    if mtype:
        stmt = stmt.where(Movement.type == mtype)
    if ref_type:
        stmt = stmt.where(Movement.ref_type == ref_type)
    if ref_id is not None:
        stmt = stmt.where(Movement.ref_id == ref_id)
    return paginate(db, stmt.order_by(Movement.id.desc()), params)


def availability(db: Session, product_id: int) -> dict:
    row = db.execute(select(func.coalesce(func.sum(Stock.on_hand), 0),
                            func.coalesce(func.sum(Stock.reserved), 0))
                     .where(Stock.product_id == product_id)).one()
    on_hand, reserved = Decimal(str(row[0])), Decimal(str(row[1]))
    return {"product_id": product_id, "on_hand": on_hand, "reserved": reserved,
            "available": on_hand - reserved}


def order_reservations(db: Session, order_id: int) -> list[Reservation]:
    return list(db.scalars(select(Reservation).where(Reservation.order_id == order_id)
                           .order_by(Reservation.id)))


# ---------------- reservation
def _allocate(db: Session, product_id: int, need: Decimal):
    """Aguulah (best-fit): neg aguulahaas hureh bol hamgiin jijig hureltsetei n, ugui bol ikheesee n daguulna."""
    stmt = (select(Stock).join(Location, Location.id == Stock.location_id)
            .where(Stock.product_id == product_id, Location.type == "warehouse",
                   Location.deleted_at.is_(None), Location.is_active.is_(True)))
    cands = [s for s in db.scalars(stmt) if s.on_hand - s.reserved > 0]
    single = sorted((s for s in cands if s.on_hand - s.reserved >= need), key=lambda s: (s.on_hand - s.reserved, s.id))
    if single:
        return [(single[0], need)], ZERO
    allocs, rest = [], need
    for s in sorted(cands, key=lambda s: (-(s.on_hand - s.reserved), s.id)):
        take = min(s.on_hand - s.reserved, rest)
        allocs.append((s, take))
        rest -= take
        if rest <= 0:
            break
    return allocs, rest


def _reserve_product(db: Session, order_id: int, product_id: int, need: Decimal) -> Decimal:
    allocs, rest = _allocate(db, product_id, need)
    for st, q in allocs:
        st.reserved = st.reserved + q
        db.add(Reservation(order_id=order_id, product_id=product_id, location_id=st.location_id,
                           quantity=q, status="active"))
    return rest


def reserve_for_order(db: Session, order_id: int, lines: list[dict]) -> list[dict]:
    """Idempotent: order-t reserve baival dahin hiihgui. Butsaah: hureehgui (short) jagsaalt."""
    if db.scalar(select(Reservation.id).where(Reservation.order_id == order_id).limit(1)):
        return []
    need: dict[int, Decimal] = {}
    for ln in lines:
        need[ln["product_id"]] = need.get(ln["product_id"], ZERO) + Decimal(str(ln["quantity"]))
    shortages = []
    for pid, qty in need.items():
        rest = _reserve_product(db, order_id, pid, qty)
        if rest > 0:
            db.add(Reservation(order_id=order_id, product_id=pid, location_id=None, quantity=rest, status="short"))
            shortages.append({"product_id": pid, "quantity": str(rest)})
    db.commit()
    return shortages


def retry_reserve(db: Session, order_id: int) -> list[dict]:
    rows = order_reservations(db, order_id)
    if not rows:
        raise NotFoundError("Ene zahialgad reserve oldsongui")
    shortages = []
    for r in rows:
        if r.status != "short":
            continue
        rest = _reserve_product(db, order_id, r.product_id, r.quantity)
        if rest > 0:
            r.quantity = rest
            shortages.append({"product_id": r.product_id, "quantity": str(rest)})
        else:
            db.delete(r)
    db.commit()
    return shortages


def release_for_order(db: Session, order_id: int) -> None:
    for r in order_reservations(db, order_id):
        if r.status == "active":
            st = _stock(db, r.location_id, r.product_id)
            st.reserved = st.reserved - r.quantity
            r.status = "released"
        elif r.status == "short":
            r.status = "released"
    db.commit()


def ship_for_order(db: Session, order_id: int) -> list[dict]:
    shortages = []
    for r in order_reservations(db, order_id):
        if r.status == "active":
            apply_movement(db, location_id=r.location_id, product_id=r.product_id, mtype="out",
                           delta=-r.quantity, ref_type="order", ref_id=order_id, from_reserved=r.quantity)
            r.status = "consumed"
        elif r.status == "short":
            shortages.append({"product_id": r.product_id, "quantity": str(r.quantity)})
    db.commit()
    return shortages


# ---------------- event handlers (orders-oos)
def _emit_shortage(order_id: int, shortages: list[dict], stage: str) -> None:
    if shortages:
        events.publish("stock.shortage", {"order_id": order_id, "shortages": shortages, "stage": stage})


@events.subscribe("order.confirmed")
def on_order_confirmed(p: dict) -> None:
    with SessionLocal() as db:
        _emit_shortage(p["order_id"], reserve_for_order(db, p["order_id"], p["lines"]), "confirmed")


@events.subscribe("order.cancelled")
def on_order_cancelled(p: dict) -> None:
    with SessionLocal() as db:
        release_for_order(db, p["order_id"])


@events.subscribe("order.shipped")
def on_order_shipped(p: dict) -> None:
    with SessionLocal() as db:
        _emit_shortage(p["order_id"], ship_for_order(db, p["order_id"]), "shipped")
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
