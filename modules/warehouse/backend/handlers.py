"""Orders-iin event-iig sonsoj reserve / release / hasalt hiine."""
from core import events
from core.database import SessionLocal

from . import service


@events.subscribe("order.confirmed")
def on_confirmed(payload: dict) -> None:
    with SessionLocal() as db:
        service.reserve_order(db, payload["order_id"], payload.get("lines", []))


@events.subscribe("order.cancelled")
def on_cancelled(payload: dict) -> None:
    with SessionLocal() as db:
        service.release_order(db, payload["order_id"])


@events.subscribe("order.shipped")
def on_shipped(payload: dict) -> None:
    with SessionLocal() as db:
        service.consume_order(db, payload["order_id"], payload.get("lines", []))
