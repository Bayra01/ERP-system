"""Hariltsagchiin portal: "Hereglegch" uuregtei hun zuvhun UURIIN hariltsagchiin medeellig harna.

User.customer_id -> md_customers. Holbogdoogui bol anh hereglehed uuriin nereer hariltsagch uusgene.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import NotFoundError
from modules.auth.backend.models import User
from modules.finance.backend import service as finance
from modules.finance.backend.models import Invoice
from modules.masterdata.backend.models import Customer, Location, Product
from modules.orders.backend.models import Order
from modules.transport.backend.models import Driver, Shipment, Trip, Vehicle


def customer_of(db: Session, user: User) -> Customer:
    c = db.get(Customer, user.customer_id) if user.customer_id else None
    if c is None or c.deleted_at is not None:
        c = Customer(code=f"U-{user.id}", name=user.full_name or user.username, type="individual")
        db.add(c)
        db.flush()
        user.customer_id = c.id
        db.commit()
    return c


def own_order(db: Session, customer: Customer, order_id: int) -> Order:
    o = db.get(Order, order_id)
    if o is None or o.customer_id != customer.id:  # busdiin zahialgyg baigaa eseh ch ilruulehgui
        raise NotFoundError("Zahialga oldsongui")
    return o


def own_location(db: Session, customer: Customer, location_id: int | None) -> Location | None:
    if location_id is None:
        return None
    loc = db.get(Location, location_id)
    if loc is None or loc.customer_id != customer.id or loc.deleted_at is not None:
        raise NotFoundError("Hurgeh hayag oldsongui")
    return loc


def tracking(db: Session, order: Order) -> dict:
    """Zahialgiin hurgeltiin baidal: shipment, aylal (mashin, jolooch, zogsoltiin bairlal), nehemjleh."""
    names = {p.id: (p.name, p.unit) for p in db.scalars(
        select(Product).where(Product.id.in_({ln.product_id for ln in order.lines})))}
    loc = db.get(Location, order.delivery_location_id) if order.delivery_location_id else None
    out = {
        "id": order.id, "order_no": order.order_no, "status": order.status, "order_date": order.order_date,
        "requested_delivery_date": order.requested_delivery_date, "notes": order.notes,
        "total_amount": float(order.total_amount),
        "delivery_location": {"name": loc.name, "address": loc.address} if loc else None,
        "lines": [{"product": names.get(ln.product_id, ("#%s" % ln.product_id, ""))[0],
                   "unit": names.get(ln.product_id, ("", ""))[1], "quantity": float(ln.quantity),
                   "unit_price": float(ln.unit_price), "line_total": float(ln.line_total)} for ln in order.lines],
        "history": [{"to_status": h.to_status, "created_at": h.created_at, "note": h.note} for h in order.history],
        "shipment": None, "trip": None, "invoice": None,
    }
    sh = db.scalar(select(Shipment).where(Shipment.order_id == order.id))
    if sh:
        out["shipment"] = {"status": sh.status, "ready": sh.ready, "delivered_at": sh.delivered_at,
                           "failed_reason": sh.failed_reason}
        trip = db.get(Trip, sh.trip_id) if sh.trip_id else None
        if trip and trip.status != "cancelled":
            stops = db.scalars(select(Shipment).where(Shipment.trip_id == trip.id)
                               .order_by(Shipment.stop_sequence, Shipment.id)).all()
            pos = next((i for i, s in enumerate(stops, start=1) if s.id == sh.id), None)
            v, d = db.get(Vehicle, trip.vehicle_id), db.get(Driver, trip.driver_id)
            live = trip.status == "in_progress"
            out["trip"] = {
                "trip_no": trip.trip_no, "status": trip.status, "planned_date": trip.planned_date,
                "started_at": trip.started_at, "vehicle_plate": v.plate_no if v else None,
                "driver_name": d.full_name if d else None,
                "driver_phone": d.phone if d and live else None,  # zuvhun zamd yavah uyed
                "stops_total": len(stops), "my_stop": pos,
                "stops_done": sum(s.status in ("delivered", "failed") for s in stops),
            }
    inv = db.scalar(select(Invoice).where(Invoice.order_id == order.id))
    if inv:
        out["invoice"] = {"number": inv.number, "amount": float(inv.amount), "paid": float(inv.paid),
                          "balance": float(inv.amount - inv.paid), "due": inv.due,
                          "status": finance.invoice_status(inv)}
    return out
