<<<<<<< HEAD
"""Zahialgiin business logic: uusgeh, zasah, status machine, event."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from core import events
from core.audit import log_action
from core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from core.permissions import has_permission
from modules.auth.backend.models import User
from modules.masterdata.backend.models import Customer, Location, Product

from .models import Order, OrderLine, OrderStatusHistory
from .schemas import LineIn

ALLOWED: dict[str, set[str]] = {
=======
"""Orders: uusgeh, zasah, status machine, event.

Events (bukh n payload: order_id, order_no, customer_id, from_status, lines=[{product_id, quantity}]):
  order.confirmed | order.picking | order.shipped | order.delivered | order.cancelled
-> Warehouse: confirmed-d stock reserve, cancelled-d release, shipped-d stock hasna
-> Finance:   delivered-d invoice uusgene
-> Notifications: status burt medegdel
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core import events
from core.audit import log_action
from core.database import SessionLocal
from core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from core.pagination import PageParams, paginate
from core.permissions import has_permission
from modules.masterdata.backend.models import Customer, Location, Product

from .models import Order, OrderLine, OrderStatusHistory
from .schemas import OrderCreate, OrderLineIn, OrderUpdate

ALLOWED = {
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    "draft": {"confirmed", "cancelled"},
    "confirmed": {"picking", "cancelled"},
    "picking": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}
<<<<<<< HEAD
=======
# Ali status ruu shiljihed yamar erh shaardah ve
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
TRANSITION_PERMISSION = {
    "confirmed": "orders:write",
    "cancelled": "orders:write",
    "picking": "orders:fulfil",
    "shipped": "orders:fulfil",
    "delivered": "orders:deliver",
}


<<<<<<< HEAD
def get_order(db: Session, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise NotFoundError(f"Zahialga #{order_id} oldsongui")
    return order


def _check_refs(db: Session, customer_id: int, location_id: int | None) -> None:
    c = db.get(Customer, customer_id)
    if c is None or c.deleted_at is not None or not c.is_active:
        raise UnprocessableError(f"Harilcagch #{customer_id} oldsongui esvel idevhgui")
    if location_id is not None:
        loc = db.get(Location, location_id)
        if loc is None or loc.deleted_at is not None:
            raise UnprocessableError(f"Bairshil #{location_id} oldsongui")


def _build_lines(db: Session, lines: list[LineIn]) -> list[OrderLine]:
=======
class ValidationFailed(AppError):
    status_code, code = 422, "validation_error"


def get_order(db: Session, order_id: int) -> Order:
    order = db.scalar(select(Order).where(Order.id == order_id)
                      .options(selectinload(Order.lines), selectinload(Order.history)))
    if order is None:
        raise NotFoundError("Zahialga oldsongui")
    return order


def _validate_refs(db: Session, customer_id: int, location_id: int | None) -> None:
    c = db.get(Customer, customer_id)
    if c is None or c.deleted_at is not None or not c.is_active:
        raise ValidationFailed("Hariltsagch oldsongui esvel idevhgui baina")
    if location_id is not None:
        loc = db.get(Location, location_id)
        if loc is None or loc.deleted_at is not None:
            raise ValidationFailed("Hurgeh hayag oldsongui")
        if loc.customer_id is not None and loc.customer_id != customer_id:
            raise ValidationFailed("Ene hayag ene hariltsagchid hamaarahgui baina")


def _build_lines(db: Session, lines: list[OrderLineIn]) -> list[OrderLine]:
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    out = []
    for ln in lines:
        p = db.get(Product, ln.product_id)
        if p is None or p.deleted_at is not None or not p.is_active:
<<<<<<< HEAD
            raise UnprocessableError(f"Baraa #{ln.product_id} oldsongui esvel idevhgui")
=======
            raise ValidationFailed(f"Baraa oldsongui esvel idevhgui: id={ln.product_id}")
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
        price = ln.unit_price if ln.unit_price is not None else Decimal(p.price)
        out.append(OrderLine(product_id=p.id, quantity=ln.quantity, unit_price=price,
                             line_total=(ln.quantity * price).quantize(Decimal("0.01"))))
    return out


<<<<<<< HEAD
def _set_lines(order: Order, lines: list[OrderLine]) -> None:
    order.lines = lines
    order.total_amount = sum((ln.line_total for ln in lines), Decimal(0))


def create_order(db: Session, data, user: User) -> Order:
    _check_refs(db, data.customer_id, data.delivery_location_id)
    order = Order(customer_id=data.customer_id, delivery_location_id=data.delivery_location_id,
                  requested_delivery_date=data.requested_delivery_date, notes=data.notes,
                  status="draft", created_by=user.id)
    _set_lines(order, _build_lines(db, data.lines))
    db.add(order)
    db.flush()
    order.order_no = f"ORD-{order.order_date:%Y%m}-{order.id:06d}"
    order.history.append(OrderStatusHistory(from_status=None, to_status="draft", user_id=user.id))
    db.commit()
    log_action(db, user.id, "create", "orders.Order", order.id)
    return order


def update_order(db: Session, order: Order, data, user: User) -> Order:
    if order.status != "draft":
        raise ConflictError("Zovhon noorog (draft) zahialgiig zasna")
    fields = data.model_dump(exclude_unset=True)
    customer_id = fields.get("customer_id") or order.customer_id
    location_id = fields.get("delivery_location_id", order.delivery_location_id)
    _check_refs(db, customer_id, location_id)
    for k in ("customer_id", "delivery_location_id", "requested_delivery_date", "notes"):
        if k in fields and not (k == "customer_id" and fields[k] is None):
            setattr(order, k, fields[k])
    if data.lines is not None:
        _set_lines(order, _build_lines(db, data.lines))
    db.commit()
    log_action(db, user.id, "update", "orders.Order", order.id, {"fields": sorted(fields)})
    return order


def delete_order(db: Session, order: Order, user: User) -> None:
    if order.status != "draft":
        raise ConflictError("Zovhon noorog (draft) zahialgiig ustgana")
    oid = order.id
    db.delete(order)
    db.commit()
    log_action(db, user.id, "delete", "orders.Order", oid)


def event_payload(order: Order, from_status: str | None) -> dict:
    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "customer_id": order.customer_id,
        "from_status": from_status,
        "delivery_location_id": order.delivery_location_id,
        "lines": [{"product_id": ln.product_id, "quantity": float(ln.quantity),
                   "unit_price": float(ln.unit_price)} for ln in order.lines],
        "total_amount": float(order.total_amount),
    }


def change_status(db: Session, order: Order, to: str, user: User | None,
                  note: str | None = None) -> Order:
    """user=None -> sistemiin dotood shiljilt (event-ees), erh shalgahgui."""
    if to not in ALLOWED.get(order.status, set()):
        raise ConflictError(f"'{order.status}' -> '{to}' shiljilt bolomjgui")
    if user is not None and not has_permission(user.role, TRANSITION_PERMISSION[to]):
        raise ForbiddenError(f"Erh hureltsehgui: {TRANSITION_PERMISSION[to]}")
    frm = order.status
    order.status = to
    order.history.append(OrderStatusHistory(from_status=frm, to_status=to,
                                            user_id=user.id if user else None, note=note))
    db.commit()
    log_action(db, user.id if user else None, "status", "orders.Order", order.id,
               {"from": frm, "to": to})
    events.publish(f"order.{to}", event_payload(order, frm))
    db.refresh(order)  # handler-uud uur session-oor uurchilsun baij magadgui
    return order


def list_stmt(status: str | None, q: str | None, customer_id: int | None):
    stmt = select(Order)
    if status:
        stmt = stmt.where(Order.status == status)
    if q:
        stmt = stmt.where(Order.order_no.ilike(f"%{q}%"))
    if customer_id:
        stmt = stmt.where(Order.customer_id == customer_id)
    return stmt.order_by(Order.id.desc())
=======
def _recalc(order: Order) -> None:
    order.total_amount = sum((l.line_total for l in order.lines), Decimal("0"))


def create_order(db: Session, data: OrderCreate, user_id: int | None) -> Order:
    _validate_refs(db, data.customer_id, data.delivery_location_id)
    order = Order(customer_id=data.customer_id, delivery_location_id=data.delivery_location_id,
                  requested_delivery_date=data.requested_delivery_date, notes=data.notes,
                  created_by=user_id, status="draft")
    order.lines = _build_lines(db, data.lines)
    _recalc(order)
    order.history.append(OrderStatusHistory(from_status=None, to_status="draft", user_id=user_id))
    db.add(order)
    db.flush()
    order.order_no = f"ORD-{order.order_date:%Y%m}-{order.id:06d}"
    db.commit()
    log_action(db, user_id, "create", "orders.Order", order.id)
    return get_order(db, order.id)


def update_order(db: Session, order_id: int, data: OrderUpdate, user_id: int | None) -> Order:
    order = get_order(db, order_id)
    if order.status != "draft":
        raise ConflictError("Zuvhun draft zahialgiig zasna")
    values = data.model_dump(exclude_unset=True)
    lines = values.pop("lines", None)
    cust = values.get("customer_id", order.customer_id)
    loc = values["delivery_location_id"] if "delivery_location_id" in values else order.delivery_location_id
    _validate_refs(db, cust, loc)
    for k, v in values.items():
        setattr(order, k, v)
    if lines is not None:
        order.lines.clear()
        db.flush()
        order.lines.extend(_build_lines(db, data.lines))
    _recalc(order)
    db.commit()
    log_action(db, user_id, "update", "orders.Order", order.id)
    return get_order(db, order_id)


def delete_draft(db: Session, order_id: int, user_id: int | None) -> None:
    order = get_order(db, order_id)
    if order.status != "draft":
        raise ConflictError("Zuvhun draft zahialgiig ustgana. Busdiig 'cancelled' bolgono uu")
    db.delete(order)
    db.commit()
    log_action(db, user_id, "delete", "orders.Order", order_id)


def change_status(db: Session, order_id: int, to: str, role: str, user_id: int | None,
                  note: str | None = None) -> Order:
    order = get_order(db, order_id)
    frm = order.status
    if to not in ALLOWED[frm]:
        raise ConflictError(f"'{frm}' -> '{to}' shiljilt zuvshuurugdohgui")
    perm = TRANSITION_PERMISSION[to]
    if not has_permission(role, perm):
        raise ForbiddenError(f"Erh hureltsehgui: {perm}")
    if to == "confirmed" and not order.lines:
        raise ConflictError("Mor hooson zahialgiig batalgaajuulah bolomjgui")

    order.status = to
    order.history.append(OrderStatusHistory(from_status=frm, to_status=to, user_id=user_id, note=note))
    db.commit()
    log_action(db, user_id, "status", "orders.Order", order.id, {"from": frm, "to": to})

    events.publish(f"order.{to}", {
        "order_id": order.id, "order_no": order.order_no, "customer_id": order.customer_id,
        "from_status": frm, "delivery_location_id": order.delivery_location_id,
        "lines": [{"product_id": l.product_id, "quantity": str(l.quantity)} for l in order.lines],
        "total_amount": str(order.total_amount),
    })
    return get_order(db, order_id)


def list_orders(db: Session, params: PageParams, status: str | None = None,
                customer_id: int | None = None, q: str | None = None,
                date_from: datetime | None = None, date_to: datetime | None = None):
    stmt = select(Order)
    if status:
        stmt = stmt.where(Order.status == status)
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if q:
        stmt = stmt.where(Order.order_no.ilike(f"%{q}%"))
    if date_from:
        stmt = stmt.where(Order.order_date >= date_from)
    if date_to:
        stmt = stmt.where(Order.order_date <= date_to)
    return paginate(db, stmt.order_by(Order.id.desc()), params)


# ---- Transport-oos: jolooch hurgelt hiisen -> zahialga 'delivered'
@events.subscribe("shipment.delivered")
def on_shipment_delivered(p: dict) -> None:
    with SessionLocal() as db:
        order = db.get(Order, p["order_id"])
        if order is None or order.status != "shipped":
            return
        change_status(db, order.id, "delivered", "admin", p.get("user_id"), "Hurgelt hiigdlee (transport)")
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
