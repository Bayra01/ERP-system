"""Hurgelt (shipment), aylal (trip) logic."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core import events
from core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from core.mixins import utcnow
from core.permissions import Role, has_permission
from modules.auth.backend.models import User
from modules.masterdata.backend.models import Location, Product

from .models import Driver, Shipment, Trip, Vehicle

ACTIVE_TRIP = ("planned", "in_progress")
ASSIGNABLE = ("pending", "failed")


def get_or_404(db: Session, model, obj_id: int, label: str):
    obj = db.get(model, obj_id)
    if obj is None or getattr(obj, "deleted_at", None) is not None:
        raise NotFoundError(f"{label} #{obj_id} oldsongui")
    return obj


def _weights(db: Session, lines: list[dict]) -> tuple[float, float]:
    kg = m3 = 0.0
    for ln in lines:
        p = db.get(Product, ln["product_id"])
        if p is not None:
            kg += (p.weight_kg or 0) * float(ln["quantity"])
            m3 += (p.volume_m3 or 0) * float(ln["quantity"])
    return round(kg, 3), round(m3, 4)


# ---------------- Order event-ees
def upsert_shipment(db: Session, payload: dict, ready: bool) -> Shipment:
    sh = db.scalar(select(Shipment).where(Shipment.order_id == payload["order_id"]))
    kg, m3 = _weights(db, payload.get("lines", []))
    if sh is None:
        sh = Shipment(order_id=payload["order_id"], customer_id=payload.get("customer_id"),
                      location_id=payload.get("delivery_location_id"), status="pending",
                      ready=ready, weight_kg=kg, volume_m3=m3)
        db.add(sh)
    else:
        sh.ready = sh.ready or ready
        if sh.status == "cancelled":
            sh.status = "pending"
    db.commit()
    return sh


def cancel_shipment(db: Session, order_id: int) -> None:
    sh = db.scalar(select(Shipment).where(Shipment.order_id == order_id))
    if sh is None or sh.status in ("delivered", "in_transit"):
        return
    sh.status, sh.trip_id, sh.stop_sequence = "cancelled", None, None
    db.commit()


# ---------------- Trip
def trip_shipments(db: Session, trip_id: int) -> list[Shipment]:
    return list(db.scalars(select(Shipment).where(Shipment.trip_id == trip_id)
                           .order_by(Shipment.stop_sequence.nulls_last(), Shipment.id)))


def _check_capacity(vehicle: Vehicle, shipments: list[Shipment]) -> None:
    kg = sum(s.weight_kg for s in shipments)
    m3 = sum(s.volume_m3 for s in shipments)
    if vehicle.capacity_kg and kg > vehicle.capacity_kg:
        raise ConflictError(f"Achaa {kg:g} kg > mashinii daats {vehicle.capacity_kg:g} kg")
    if vehicle.capacity_m3 and m3 > vehicle.capacity_m3:
        raise ConflictError(f"Ezelhuun {m3:g} m3 > mashinii bagtaamj {vehicle.capacity_m3:g} m3")


def _check_refs(db: Session, vehicle_id: int, driver_id: int, depot_id: int | None):
    v = get_or_404(db, Vehicle, vehicle_id, "Mashin")
    if not v.is_active or v.status == "maintenance":
        raise ConflictError(f"{v.plate_no} mashin ashiglah bolomjgui ({v.status})")
    d = get_or_404(db, Driver, driver_id, "Jolooch")
    if not d.is_active:
        raise ConflictError(f"{d.full_name} jolooch idevhgui")
    if depot_id is not None:
        loc = db.get(Location, depot_id)
        if loc is None or loc.deleted_at is not None:
            raise UnprocessableError(f"Bairshil #{depot_id} oldsongui")
    return v, d


def _assign(db: Session, trip: Trip, vehicle: Vehicle, shipment_ids: list[int]) -> None:
    ids = list(dict.fromkeys(shipment_ids))
    shipments = list(db.scalars(select(Shipment).where(Shipment.id.in_(ids)))) if ids else []
    if len(shipments) != len(ids):
        raise UnprocessableError("Zarim hurgelt oldsongui")
    for s in shipments:
        if s.trip_id != trip.id and s.status not in ASSIGNABLE:
            raise ConflictError(f"Hurgelt #{s.id} onooh bolomjgui ({s.status})")
    _check_capacity(vehicle, shipments)
    for old in trip_shipments(db, trip.id):  # hasagdsan-iig sullana
        if old.id not in ids:
            old.trip_id, old.stop_sequence, old.status = None, None, "pending"
    order = {sid: i for i, sid in enumerate(ids, start=1)}
    for s in shipments:
        s.trip_id, s.status, s.failed_reason = trip.id, "assigned", None
        s.stop_sequence = order[s.id]
    trip.total_distance_km = None  # marshrut dahin tootsno


def create_trip(db: Session, data, user: User) -> Trip:
    v, _ = _check_refs(db, data.vehicle_id, data.driver_id, data.depot_location_id)
    trip = Trip(vehicle_id=data.vehicle_id, driver_id=data.driver_id,
                planned_date=data.planned_date, depot_location_id=data.depot_location_id,
                notes=data.notes, status="planned", created_by=user.id)
    db.add(trip)
    db.flush()
    trip.trip_no = f"TR-{trip.planned_date:%Y%m}-{trip.id:05d}"
    _assign(db, trip, v, data.shipment_ids)
    db.commit()
    return trip


def update_trip(db: Session, trip: Trip, data) -> Trip:
    if trip.status != "planned":
        raise ConflictError("Zovhon tuluvluguunii (planned) aylliig zasna")
    fields = data.model_dump(exclude_unset=True)
    ids = fields.pop("shipment_ids", None)
    v, _ = _check_refs(db, fields.get("vehicle_id") or trip.vehicle_id,
                       fields.get("driver_id") or trip.driver_id,
                       fields.get("depot_location_id", trip.depot_location_id))
    for k, val in fields.items():
        if val is not None or k in ("depot_location_id", "notes"):
            setattr(trip, k, val)
    if ids is not None:
        _assign(db, trip, v, ids)
    else:
        _check_capacity(v, trip_shipments(db, trip.id))
    db.commit()
    return trip


def start_trip(db: Session, trip: Trip) -> Trip:
    if trip.status != "planned":
        raise ConflictError(f"'{trip.status}' aylliig ehluulehgui")
    shipments = trip_shipments(db, trip.id)
    if not_ready := [s.order_id for s in shipments if not s.ready]:
        raise ConflictError(f"Zahialga ilgeegdeegui baina: {not_ready}")
    v = db.get(Vehicle, trip.vehicle_id)
    _check_capacity(v, shipments)
    busy = select(func.count()).select_from(Trip).where(Trip.status == "in_progress",
                                                        Trip.id != trip.id)
    if db.scalar(busy.where(Trip.vehicle_id == trip.vehicle_id)):
        raise ConflictError(f"{v.plate_no} mashin uur aylald yavj baina")
    if db.scalar(busy.where(Trip.driver_id == trip.driver_id)):
        raise ConflictError("Jolooch uur aylald yavj baina")
    trip.status, trip.started_at = "in_progress", utcnow()
    v.status = "on_trip"
    for s in shipments:
        s.status = "in_transit"
    db.commit()
    events.publish("trip.started", {"trip_id": trip.id, "trip_no": trip.trip_no,
                                    "order_ids": [s.order_id for s in shipments]})
    return trip


def cancel_trip(db: Session, trip: Trip) -> Trip:
    if trip.status != "planned":
        raise ConflictError("Zovhon tuluvluguunii (planned) aylliig tsutsalna")
    for s in trip_shipments(db, trip.id):
        s.trip_id, s.stop_sequence, s.status = None, None, "pending"
    trip.status = "cancelled"
    db.commit()
    return trip


def _maybe_complete(db: Session, trip: Trip, force: bool = False) -> bool:
    shipments = trip_shipments(db, trip.id)
    if any(s.status == "in_transit" for s in shipments) and not force:
        return False
    trip.status, trip.completed_at = "completed", utcnow()
    v = db.get(Vehicle, trip.vehicle_id)
    if v.status == "on_trip":
        v.status = "available"
    db.commit()
    events.publish("trip.completed", {
        "trip_id": trip.id, "trip_no": trip.trip_no,
        "delivered": [s.order_id for s in shipments if s.status == "delivered"],
        "failed": [s.order_id for s in shipments if s.status == "failed"]})
    return True


def complete_trip(db: Session, trip: Trip) -> Trip:
    if trip.status != "in_progress":
        raise ConflictError("Zovhon yavj bui (in_progress) aylliig duusgana")
    if any(s.status == "in_transit" for s in trip_shipments(db, trip.id)):
        raise ConflictError("Shiidegdeegui hurgelt baina")
    _maybe_complete(db, trip)
    return trip


def check_driver_access(db: Session, user: User, trip: Trip) -> None:
    """Jolooch zovhon uuriin aylal, busad transport:write erhtei baih."""
    if user.role == Role.DRIVER.value:
        d = db.get(Driver, trip.driver_id)
        if d is None or d.user_id != user.id:
            raise ForbiddenError("Ene tany aylal bish")
    elif not has_permission(user.role, "transport:write"):
        raise ForbiddenError("Erh hureltsehgui: transport:write")


def _resolve(db: Session, sh: Shipment, user: User) -> Trip:
    if sh.status != "in_transit" or sh.trip_id is None:
        raise ConflictError(f"Hurgelt #{sh.id} zamd yavaagui ({sh.status})")
    trip = db.get(Trip, sh.trip_id)
    check_driver_access(db, user, trip)
    return trip


def deliver(db: Session, sh: Shipment, user: User, note: str | None = None) -> Shipment:
    trip = _resolve(db, sh, user)
    sh.status, sh.delivered_at = "delivered", utcnow()
    if note:
        sh.note = note
    db.commit()
    events.publish("shipment.delivered", {"shipment_id": sh.id, "order_id": sh.order_id,
                                          "trip_id": trip.id})
    _maybe_complete(db, trip)
    return sh


def fail(db: Session, sh: Shipment, user: User, reason: str) -> Shipment:
    trip = _resolve(db, sh, user)
    sh.status, sh.failed_reason = "failed", reason
    db.commit()
    events.publish("shipment.failed", {"shipment_id": sh.id, "order_id": sh.order_id,
                                       "trip_id": trip.id, "reason": reason})
    _maybe_complete(db, trip)
    return sh


def trip_view(db: Session, trip: Trip, detail: bool = False) -> dict:
    shipments = trip_shipments(db, trip.id)
    v, d = db.get(Vehicle, trip.vehicle_id), db.get(Driver, trip.driver_id)
    depot = db.get(Location, trip.depot_location_id) if trip.depot_location_id else None
    out = {c.key: getattr(trip, c.key) for c in Trip.__table__.columns}
    out.update(vehicle_plate=v.plate_no if v else None, driver_name=d.full_name if d else None,
               depot_name=depot.name if depot else None, stops=len(shipments),
               delivered=sum(s.status == "delivered" for s in shipments),
               weight_kg=round(sum(s.weight_kg for s in shipments), 3))
    if detail:
        out["shipments"] = shipments
    return out
