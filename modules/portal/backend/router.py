"""/api/portal - hariltsagchiin portal ("Hereglegch" uureg, portal:use).

Buh endpoint zuvhun nevtersen hereglegchiin harilcagchiin (User.customer_id) medeellig butsaana.
"""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import events
from core.audit import log_action
from core.database import get_db
from core.deps import require_permission
from core.exceptions import ConflictError
from modules.auth.backend.models import User
from modules.masterdata.backend.models import Location, Product
from modules.orders.backend import service as orders
from modules.orders.backend.models import Order
from modules.orders.backend.schemas import LineIn, OrderCreate
from modules.transport.backend.models import Shipment

from . import service

router = APIRouter(prefix="/api/portal", tags=["Portal"])
portal_user = Depends(require_permission("portal:use"))


class AddressIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str | None = Field(None, max_length=300)
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)


class PortalLine(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)


class PortalOrderIn(BaseModel):
    delivery_location_id: int | None = None
    requested_delivery_date: datetime | None = None
    notes: str | None = Field(None, max_length=1000)
    lines: list[PortalLine] = Field(min_length=1, max_length=50)


@router.get("/me")
def portal_me(db: Session = Depends(get_db), user: User = portal_user):
    c = service.customer_of(db, user)
    return {"customer_id": c.id, "customer_code": c.code, "customer_name": c.name}


@router.get("/products")
def catalog(db: Session = Depends(get_db), user: User = portal_user):
    """Idevhtei baraa (une). Hereglegch une uurchluhgui - zahialgad baraanii une orno."""
    rows = db.scalars(select(Product).where(Product.deleted_at.is_(None), Product.is_active.is_(True))
                      .order_by(Product.name))
    return [{"id": p.id, "sku": p.sku, "name": p.name, "unit": p.unit, "price": float(p.price)} for p in rows]


@router.get("/addresses")
def addresses(db: Session = Depends(get_db), user: User = portal_user):
    c = service.customer_of(db, user)
    rows = db.scalars(select(Location).where(Location.customer_id == c.id, Location.deleted_at.is_(None))
                      .order_by(Location.id))
    return [{"id": x.id, "name": x.name, "address": x.address} for x in rows]


@router.post("/addresses", status_code=201)
def add_address(body: AddressIn, db: Session = Depends(get_db), user: User = portal_user):
    c = service.customer_of(db, user)
    loc = Location(name=body.name.strip(), address=body.address, lat=body.lat, lng=body.lng,
                   type="customer", customer_id=c.id)
    db.add(loc)
    db.commit()
    log_action(db, user.id, "create", "masterdata.Location", loc.id, {"portal": True})
    return {"id": loc.id, "name": loc.name, "address": loc.address}


@router.get("/orders")
def my_orders(db: Session = Depends(get_db), user: User = portal_user):
    c = service.customer_of(db, user)
    rows = db.scalars(select(Order).where(Order.customer_id == c.id).order_by(Order.id.desc()).limit(200)).all()
    ships = {s.order_id: s for s in db.scalars(select(Shipment).where(Shipment.order_id.in_([o.id for o in rows])))}
    names = {p.id: p.name for p in db.scalars(select(Product))}
    out = []
    for o in rows:
        first = o.lines[0] if o.lines else None
        summary = f"{names.get(first.product_id, '?')} × {float(first.quantity):g}" if first else ""
        if len(o.lines) > 1:
            summary += f" +{len(o.lines) - 1}"
        sh = ships.get(o.id)
        out.append({"id": o.id, "order_no": o.order_no, "status": o.status, "order_date": o.order_date,
                    "requested_delivery_date": o.requested_delivery_date,
                    "total_amount": float(o.total_amount), "summary": summary,
                    "shipment_status": sh.status if sh else None})
    return out


@router.get("/orders/{order_id}")
def order_detail(order_id: int, db: Session = Depends(get_db), user: User = portal_user):
    c = service.customer_of(db, user)
    return service.tracking(db, service.own_order(db, c, order_id))


@router.post("/orders", status_code=201)
def place_order(body: PortalOrderIn, db: Session = Depends(get_db), user: User = portal_user):
    """Hereglegch zahialga ugnu: "draft" tuluvtei, dispetcher batalna. Une = baraanii une."""
    c = service.customer_of(db, user)
    service.own_location(db, c, body.delivery_location_id)
    data = OrderCreate(customer_id=c.id, delivery_location_id=body.delivery_location_id,
                       requested_delivery_date=body.requested_delivery_date, notes=body.notes,
                       lines=[LineIn(product_id=ln.product_id, quantity=ln.quantity) for ln in body.lines])
    order = orders.create_order(db, data, user)
    events.publish("order.submitted", {"order_id": order.id, "order_no": order.order_no,
                                       "customer_id": c.id, "customer_name": c.name,
                                       "total_amount": float(order.total_amount)})
    return service.tracking(db, order)


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = portal_user):
    """Zuvhun batlagdaagui (draft) zahialgyg hereglegch uuruu tsutsalna."""
    c = service.customer_of(db, user)
    order = service.own_order(db, c, order_id)
    if order.status != "draft":
        raise ConflictError("Batlagdsan zahialgyg tsutsalbal dispetchert handana uu")
    orders.change_status(db, order, "cancelled", None, "Hereglegch tsutsallaa")
    log_action(db, user.id, "cancel", "orders.Order", order.id, {"portal": True})
    return service.tracking(db, order)

