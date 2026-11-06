"""order.delivered -> nehemjleh."""
from sqlalchemy import select

from core import events
from core.database import SessionLocal

from . import service
from .models import Invoice


@events.subscribe("order.delivered")
def on_delivered(payload: dict) -> None:
    with SessionLocal() as db:
        if db.scalar(select(Invoice.id).where(Invoice.order_id == payload["order_id"])):
            return
        service.create_invoice(db, payload["customer_id"], payload.get("total_amount", 0), None,
                               order_id=payload["order_id"],
                               notes=f"Zahialga {payload.get('order_no') or payload['order_id']}")
