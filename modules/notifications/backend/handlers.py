"""Event -> zohih role-tei hereglegchded medegdel."""
from sqlalchemy import select

from core import events
from core.database import SessionLocal
from modules.auth.backend.models import User

from .models import Notification

# event: (role-uud, garchig, message template). admin buh medegdliig avna.
RULES: dict[str, tuple[set[str], str, str]] = {
    "order.confirmed": ({"dispatcher", "warehouse"}, "Zahialga batlagdlaa", "{order_no} - beltgeh"),
    "order.picking": ({"dispatcher"}, "Zahialga beltgegdej baina", "{order_no}"),
    "order.shipped": ({"dispatcher", "driver"}, "Zahialga ilgeegdlee", "{order_no} - hurgelt beltgen"),
    "order.delivered": ({"dispatcher", "accountant"}, "Zahialga hurgegdlee",
                        "{order_no} - nehemjleh uusne"),
    "order.cancelled": ({"dispatcher", "warehouse"}, "Zahialga tsutslagdlaa", "{order_no}"),
    "stock.shortage": ({"warehouse", "dispatcher"}, "Uldegdel dutuu",
                       "Zahialga #{order_id}: {count} baraa dutuu ({stage})"),
    "shipment.failed": ({"dispatcher"}, "Hurgelt amjiltgui", "Zahialga #{order_id}: {reason}"),
    "trip.started": ({"dispatcher"}, "Aylal ehellee", "{trip_no}"),
    "trip.completed": ({"dispatcher"}, "Aylal duuslaa", "{trip_no}"),
    "user.registered": (set(), "Shine burtgeliin huselt", "{full_name} ({username})"),  # zuvhun admin
    "order.submitted": ({"dispatcher"}, "Hariltsagch zahialga ugluu", "{order_no} - {customer_name}"),
}


class _Safe(dict):
    def __missing__(self, key):
        return "?"


# Hariltsagchiin ("Hereglegch") uuriin zahialgiin yavts: ene event-uudeer medegdel avna.
CUSTOMER_EVENTS = {"order.confirmed", "order.picking", "order.shipped", "order.delivered", "order.cancelled",
                   "trip.started"}


def _customer_users(db, event: str, payload: dict) -> list[int]:
    if event not in CUSTOMER_EVENTS:
        return []
    from modules.orders.backend.models import Order  # noqa: PLC0415 - medegdel orders-oos hamaarahgui baih
    if event == "trip.started":
        cids = set(db.scalars(select(Order.customer_id).where(Order.id.in_(payload.get("order_ids") or []))))
    else:
        cids = {payload.get("customer_id")} - {None}
    if not cids:
        return []
    return list(db.scalars(select(User.id).where(User.is_active.is_(True), User.role == "user",
                                                 User.customer_id.in_(cids))))


def _notify(event: str, payload: dict) -> None:
    roles, title, tpl = RULES[event]
    ctx = _Safe(payload, count=len(payload.get("shortages", [])))
    with SessionLocal() as db:
        users = db.scalars(select(User.id).where(User.is_active.is_(True),
                                                 User.role.in_(roles | {"admin"}))).all()
        users = list(dict.fromkeys([*users, *_customer_users(db, event, payload)]))
        for uid in users:
            db.add(Notification(user_id=uid, event=event, title=title,
                                message=tpl.format_map(ctx)[:500], data=payload))
        db.commit()


for _event in RULES:
    events.subscribe(_event)(lambda payload, _e=_event: _notify(_e, payload))
