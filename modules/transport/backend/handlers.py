"""Orders-iin event-iig sonsoj hurgelt (shipment) uusgene / shinechilne."""
from core import events
from core.database import SessionLocal

from . import service


@events.subscribe("order.picking")
def on_picking(payload: dict) -> None:
    with SessionLocal() as db:
        service.upsert_shipment(db, payload, ready=False)


@events.subscribe("order.shipped")
def on_shipped(payload: dict) -> None:
    with SessionLocal() as db:
        service.upsert_shipment(db, payload, ready=True)


@events.subscribe("order.cancelled")
def on_cancelled(payload: dict) -> None:
    with SessionLocal() as db:
        service.cancel_shipment(db, payload["order_id"])
