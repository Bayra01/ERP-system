"""Busad moduliin event-iig sonsono."""
from core import events
from core.database import SessionLocal

from . import service
from .models import Order


@events.subscribe("shipment.delivered")
def mark_delivered(payload: dict) -> None:
    with SessionLocal() as db:
        order = db.get(Order, payload.get("order_id"))
        if order is None or order.status != "shipped":
            return
        service.change_status(db, order, "delivered", None, "Teever: hurgegdsen")
