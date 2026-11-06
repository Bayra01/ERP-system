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
    "draft": {"confirmed", "cancelled"},
    "confirmed": {"picking", "cancelled"},
    "picking": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}
TRANSITION_PERMISSION = {
    "confirmed": "orders:write",
    "cancelled": "orders:write",
    "picking": "orders:fulfil",
    "shipped": "orders:fulfil",
    "delivered": "orders:deliver",
}


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
    out = []
    for ln in lines:
        p = db.get(Product, ln.product_id)
        if p is None or p.deleted_at is not None or not p.is_active:
            raise UnprocessableError(f"Baraa #{ln.product_id} oldsongui esvel idevhgui")
        price = ln.unit_price if ln.unit_price is not None else Decimal(p.price)
        out.append(OrderLine(product_id=p.id, quantity=ln.quantity, unit_price=price,
                             line_total=(ln.quantity * price).quantize(Decimal("0.01"))))
    return out


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
