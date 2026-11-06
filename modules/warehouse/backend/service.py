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
        db.add(st)
        db.flush()
    return st


def _ledger(db: Session, st: Stock, type_: str, delta: Decimal, user_id: int | None,
            ref_type: str | None = None, ref_id: int | None = None,
            note: str | None = None) -> Movement:
    st.on_hand = Decimal(st.on_hand) + delta
    mv = Movement(location_id=st.location_id, product_id=st.product_id, type=type_, quantity=delta,
                  balance_after=st.on_hand, ref_type=ref_type, ref_id=ref_id, note=note,
                  user_id=user_id)
    db.add(mv)
    return mv


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
