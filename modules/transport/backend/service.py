<<<<<<< HEAD
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
=======
"""Transport: Vehicle, Driver, Shipment (hurgeltiin zogsoltsoo), Trip (reis).

Sonsdog event:
  order.picking   -> Shipment (pending) uusgene, jin/omnoh baraanii medeelleer tootsno
  order.shipped   -> Shipment.ready = True (aguulahaas garsan, trip ehluuleh bolomjtoi)
  order.cancelled -> Shipment cancelled
Gargadag event:
  trip.started       {trip_id, trip_no, vehicle_id, driver_id, order_ids}
  shipment.delivered {shipment_id, order_id, trip_id, user_id}   -> Orders: order 'delivered' bolno
  shipment.failed    {shipment_id, order_id, trip_id, reason}
  trip.completed     {trip_id, trip_no, delivered, failed}
"""
import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core import events
from core.audit import log_action
from core.database import SessionLocal
from core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from core.pagination import PageParams, paginate
from modules.auth.backend.models import User
from modules.masterdata.backend import service as md
from modules.masterdata.backend.models import Location, Product

from .models import Driver, Shipment, Trip, Vehicle
from .schemas import DriverCreate, DriverUpdate, TripCreate, VehicleCreate, VehicleUpdate

log = logging.getLogger("erp.transport")
ACTIVE_TRIP = ("planned", "in_progress")


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------- Vehicles
def _guard_not_in_active_trip(db: Session, column, item_id: int, what: str) -> None:
    if db.scalar(select(Trip.id).where(column == item_id, Trip.status.in_(ACTIVE_TRIP)).limit(1)):
        raise ConflictError(f"{what} idevhtei trip-d baigaa tul ustgah/idevhgui bolgoh bolomjgui")


def create_vehicle(db, data: VehicleCreate, user_id):
    return md.create_item(db, Vehicle, data, "plate_no", user_id)


def update_vehicle(db, vid: int, data: VehicleUpdate, user_id):
    v = md.get_item(db, Vehicle, vid)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("is_active") is False or changes.get("status") == "maintenance":
        _guard_not_in_active_trip(db, Trip.vehicle_id, v.id, "Mashin")
    return md.update_item(db, Vehicle, vid, data, user_id)


def delete_vehicle(db, vid: int, user_id):
    _guard_not_in_active_trip(db, Trip.vehicle_id, vid, "Mashin")
    md.delete_item(db, Vehicle, vid, user_id)


# ---------------- Drivers
def _check_user_link(db: Session, user_id: int | None, exclude_driver_id: int | None = None) -> None:
    if user_id is None:
        return
    if db.get(User, user_id) is None:
        raise UnprocessableError(f"Hereglegch oldsongui: id={user_id}")
    other = db.scalar(select(Driver.id).where(Driver.user_id == user_id, Driver.deleted_at.is_(None)))
    if other and other != exclude_driver_id:
        raise ConflictError("Ene hereglegch ali hediin neg jolooch-toi holbogdson baina")


def create_driver(db, data: DriverCreate, user_id):
    _check_user_link(db, data.user_id)
    return md.create_item(db, Driver, data, None, user_id)


def update_driver(db, did: int, data: DriverUpdate, user_id):
    d = md.get_item(db, Driver, did)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("user_id"):
        _check_user_link(db, changes["user_id"], d.id)
    if changes.get("is_active") is False:
        _guard_not_in_active_trip(db, Trip.driver_id, d.id, "Jolooch")
    return md.update_item(db, Driver, did, data, user_id)


def delete_driver(db, did: int, user_id):
    _guard_not_in_active_trip(db, Trip.driver_id, did, "Jolooch")
    md.delete_item(db, Driver, did, user_id)


# ---------------- Shipments
def get_shipment(db: Session, sid: int) -> Shipment:
    s = db.get(Shipment, sid)
    if s is None:
        raise NotFoundError("Shipment oldsongui")
    return s


def list_shipments(db: Session, params: PageParams, status=None, ready=None, order_id=None, trip_id=None):
    stmt = select(Shipment)
    if status:
        stmt = stmt.where(Shipment.status == status)
    if ready is not None:
        stmt = stmt.where(Shipment.ready == ready)
    if order_id is not None:
        stmt = stmt.where(Shipment.order_id == order_id)
    if trip_id is not None:
        stmt = stmt.where(Shipment.trip_id == trip_id)
    return paginate(db, stmt.order_by(Shipment.id.desc()), params)


def update_shipment(db: Session, sid: int, data, user_id) -> Shipment:
    s = get_shipment(db, sid)
    if s.status in ("delivered", "cancelled"):
        raise ConflictError(f"'{s.status}' tuluvtei shipment-g zasah bolomjgui")
    values = data.model_dump(exclude_unset=True)
    if values.get("location_id") is not None:
        loc = db.get(Location, values["location_id"])
        if loc is None or loc.deleted_at is not None:
            raise UnprocessableError("Hayag oldsongui")
    for k, v in values.items():
        setattr(s, k, v)
    db.commit()
    log_action(db, user_id, "update", "transport.Shipment", s.id)
    return s


# ---------------- Trips
def get_trip(db: Session, trip_id: int) -> Trip:
    t = db.scalar(select(Trip).where(Trip.id == trip_id).options(selectinload(Trip.stops))
                  .execution_options(populate_existing=True))
    if t is None:
        raise NotFoundError("Trip oldsongui")
    return t


def list_trips(db: Session, params: PageParams, status=None, driver_id=None, vehicle_id=None,
               planned_date: date | None = None):
    stmt = select(Trip)
    if status:
        stmt = stmt.where(Trip.status == status)
    if driver_id is not None:
        stmt = stmt.where(Trip.driver_id == driver_id)
    if vehicle_id is not None:
        stmt = stmt.where(Trip.vehicle_id == vehicle_id)
    if planned_date:
        stmt = stmt.where(Trip.planned_date == planned_date)
    return paginate(db, stmt.order_by(Trip.id.desc()), params)


def my_trips(db: Session, user_id: int, params: PageParams):
    d = db.scalar(select(Driver).where(Driver.user_id == user_id, Driver.deleted_at.is_(None)))
    if d is None:
        raise NotFoundError("Ene hereglegch jolooch-toi holbogdoogui baina")
    return paginate(db, select(Trip).where(Trip.driver_id == d.id).order_by(Trip.planned_date.desc(), Trip.id.desc()), params)


def _check_free(db: Session, vehicle_id: int, driver_id: int, day: date, exclude: int | None = None) -> None:
    stmt = select(Trip).where(Trip.status.in_(ACTIVE_TRIP), Trip.planned_date == day,
                              (Trip.vehicle_id == vehicle_id) | (Trip.driver_id == driver_id))
    for t in db.scalars(stmt):
        if t.id != exclude:
            who = "Mashin" if t.vehicle_id == vehicle_id else "Jolooch"
            raise ConflictError(f"{who} {day} odor busad trip-d ({t.trip_no}) zahialagdsan baina")


def _attach(db: Session, trip: Trip, vehicle: Vehicle, ids: list[int]) -> None:
    ids = list(dict.fromkeys(ids))
    if not ids:
        return
    found = {s.id: s for s in db.scalars(select(Shipment).where(Shipment.id.in_(ids)))}
    for i in ids:
        s = found.get(i)
        if s is None:
            raise NotFoundError(f"Shipment oldsongui: id={i}")
        if s.status not in ("pending", "failed"):
            raise ConflictError(f"Shipment {i} '{s.status}' tuluvtei, trip-d nemehgui")
        if s.location_id is None:
            raise UnprocessableError(f"Shipment {i}-iin hurgeh hayag tohiruulaagui (PATCH /shipments/{i})")
    current = list(db.scalars(select(Shipment).where(Shipment.trip_id == trip.id, Shipment.status == "assigned")))
    kg = sum(s.weight_kg for s in current) + sum(found[i].weight_kg for i in ids)
    m3 = sum(s.volume_m3 for s in current) + sum(found[i].volume_m3 for i in ids)
    if vehicle.capacity_kg > 0 and kg > vehicle.capacity_kg:
        raise ConflictError(f"Achaa hetersen: {kg:g} kg > {vehicle.capacity_kg:g} kg")
    if vehicle.capacity_m3 > 0 and m3 > vehicle.capacity_m3:
        raise ConflictError(f"Omnoh hetersen: {m3:g} m3 > {vehicle.capacity_m3:g} m3")
    seq = max((s.stop_sequence or 0 for s in current), default=0)
    for i in ids:
        seq += 1
        s = found[i]
        s.trip_id, s.stop_sequence, s.status, s.failed_reason = trip.id, seq, "assigned", None


def _assigned(db: Session, trip_id: int) -> list[Shipment]:
    return list(db.scalars(select(Shipment).where(Shipment.trip_id == trip_id, Shipment.status == "assigned")
                           .order_by(Shipment.stop_sequence)))


def create_trip(db: Session, data: TripCreate, user_id: int | None) -> Trip:
    vehicle = md.get_item(db, Vehicle, data.vehicle_id)
    driver = md.get_item(db, Driver, data.driver_id)
    if not vehicle.is_active or vehicle.status != "available":
        raise ConflictError("Mashin ashiglah bolomjgui (idevhgui esvel zasvart)")
    if not driver.is_active:
        raise ConflictError("Jolooch idevhgui baina")
    if data.depot_location_id is not None and db.get(Location, data.depot_location_id) is None:
        raise UnprocessableError("Depot oldsongui")
    _check_free(db, vehicle.id, driver.id, data.planned_date)

    trip = Trip(vehicle_id=vehicle.id, driver_id=driver.id, depot_location_id=data.depot_location_id,
                planned_date=data.planned_date, notes=data.notes, created_by=user_id, status="planned")
    db.add(trip)
    db.flush()
    trip.trip_no = f"TRP-{data.planned_date:%Y%m}-{trip.id:06d}"
    _attach(db, trip, vehicle, data.shipment_ids)
    db.commit()
    log_action(db, user_id, "create", "transport.Trip", trip.id)
    return get_trip(db, trip.id)


def _planned_trip(db: Session, trip_id: int) -> Trip:
    t = get_trip(db, trip_id)
    if t.status != "planned":
        raise ConflictError(f"Zuvhun 'planned' trip-g zasna (odoo: {t.status})")
    return t


def add_shipments(db: Session, trip_id: int, ids: list[int], user_id) -> Trip:
    t = _planned_trip(db, trip_id)
    _attach(db, t, db.get(Vehicle, t.vehicle_id), ids)
    db.commit()
    log_action(db, user_id, "update", "transport.Trip", t.id, {"add": ids})
    return get_trip(db, trip_id)


def _resequence(db: Session, trip_id: int) -> None:
    for n, s in enumerate(_assigned(db, trip_id), 1):
        s.stop_sequence = n


def remove_shipment(db: Session, trip_id: int, sid: int, user_id) -> Trip:
    t = _planned_trip(db, trip_id)
    s = get_shipment(db, sid)
    if s.trip_id != t.id or s.status != "assigned":
        raise NotFoundError("Ene shipment ene trip-d baihgui")
    s.trip_id, s.stop_sequence, s.status = None, None, "pending"
    db.flush()
    _resequence(db, trip_id)
    db.commit()
    log_action(db, user_id, "update", "transport.Trip", t.id, {"remove": sid})
    return get_trip(db, trip_id)


def reorder(db: Session, trip_id: int, ids: list[int], user_id) -> Trip:
    t = _planned_trip(db, trip_id)
    current = {s.id: s for s in _assigned(db, trip_id)}
    if sorted(ids) != sorted(current) or len(set(ids)) != len(ids):
        raise UnprocessableError("Jagsaalt trip-iin buh shipment-g tadaa neg l udaa aguulah ёстой")
    for n, i in enumerate(ids, 1):
        current[i].stop_sequence = n
    db.commit()
    log_action(db, user_id, "update", "transport.Trip", t.id, {"order": ids})
    return get_trip(db, trip_id)


def cancel_trip(db: Session, trip_id: int, user_id) -> Trip:
    t = _planned_trip(db, trip_id)
    for s in _assigned(db, trip_id):
        s.trip_id, s.stop_sequence, s.status = None, None, "pending"
    t.status = "cancelled"
    db.commit()
    log_action(db, user_id, "cancel", "transport.Trip", t.id)
    return get_trip(db, trip_id)


def start_trip(db: Session, trip_id: int, user_id) -> Trip:
    t = _planned_trip(db, trip_id)
    stops = _assigned(db, trip_id)
    if not stops:
        raise ConflictError("Shipment-gui trip-g ehluuleh bolomjgui")
    not_ready = [s.order_id for s in stops if not s.ready]
    if not_ready:
        raise ConflictError(f"Aguulahaas garaagui (order 'shipped' bish) zahialga: {not_ready}")
    vehicle = db.get(Vehicle, t.vehicle_id)
    if not vehicle.is_active or vehicle.status != "available":
        raise ConflictError("Mashin ashiglah bolomjgui")
    t.status, t.started_at = "in_progress", _now()
    db.commit()
    log_action(db, user_id, "start", "transport.Trip", t.id)
    events.publish("trip.started", {"trip_id": t.id, "trip_no": t.trip_no, "vehicle_id": t.vehicle_id,
                                    "driver_id": t.driver_id, "order_ids": [s.order_id for s in stops]})
    return get_trip(db, trip_id)


def _check_drive_rights(db: Session, trip: Trip, user) -> None:
    if user.role == "driver":
        d = db.get(Driver, trip.driver_id)
        if d is None or d.user_id != user.id:
            raise ForbiddenError("Ene trip tany bish")


def _resolve(db: Session, sid: int, user, to: str, reason: str | None, note: str | None) -> Shipment:
    s = get_shipment(db, sid)
    if s.status != "assigned" or s.trip_id is None:
        raise ConflictError(f"Shipment '{s.status}' tuluvtei, '{to}' bolgoh bolomjgui")
    trip = db.get(Trip, s.trip_id)
    if trip.status != "in_progress":
        raise ConflictError("Trip ehleegui baina (in_progress bish)")
    _check_drive_rights(db, trip, user)
    s.status = to
    if to == "delivered":
        s.delivered_at = _now()
        s.note = note or s.note
    else:
        s.failed_reason = reason
    db.commit()
    log_action(db, user.id, to, "transport.Shipment", s.id, {"order_id": s.order_id})
    if to == "delivered":
        events.publish("shipment.delivered", {"shipment_id": s.id, "order_id": s.order_id,
                                              "trip_id": trip.id, "user_id": user.id})
    else:
        events.publish("shipment.failed", {"shipment_id": s.id, "order_id": s.order_id,
                                           "trip_id": trip.id, "reason": reason})
    _maybe_complete(db, trip.id)
    return s


def deliver(db: Session, sid: int, user, note: str | None = None) -> Shipment:
    return _resolve(db, sid, user, "delivered", None, note)


def fail(db: Session, sid: int, user, reason: str) -> Shipment:
    return _resolve(db, sid, user, "failed", reason, None)


def _maybe_complete(db: Session, trip_id: int) -> None:
    trip = get_trip(db, trip_id)
    if trip.status != "in_progress" or any(s.status == "assigned" for s in trip.stops):
        return
    trip.status, trip.completed_at = "completed", _now()
    db.commit()
    done = sum(1 for s in trip.stops if s.status == "delivered")
    bad = sum(1 for s in trip.stops if s.status == "failed")
    events.publish("trip.completed", {"trip_id": trip.id, "trip_no": trip.trip_no, "delivered": done, "failed": bad})


# ---------------- event handlers (orders-oos)
@events.subscribe("order.picking")
def on_order_picking(p: dict) -> None:
    with SessionLocal() as db:
        if db.scalar(select(Shipment.id).where(Shipment.order_id == p["order_id"])):
            return
        kg = m3 = 0.0
        for ln in p.get("lines", []):
            prod = db.get(Product, ln["product_id"])
            if prod:
                q = float(ln["quantity"])
                kg += q * (prod.weight_kg or 0)
                m3 += q * (prod.volume_m3 or 0)
        db.add(Shipment(order_id=p["order_id"], customer_id=p.get("customer_id"),
                        location_id=p.get("delivery_location_id"), weight_kg=kg, volume_m3=m3))
        db.commit()


@events.subscribe("order.shipped")
def on_order_shipped(p: dict) -> None:
    with SessionLocal() as db:
        s = db.scalar(select(Shipment).where(Shipment.order_id == p["order_id"]))
        if s is None:
            log.warning("order.shipped: shipment oldsongui order=%s", p["order_id"])
            return
        s.ready = True
        db.commit()


@events.subscribe("order.cancelled")
def on_order_cancelled(p: dict) -> None:
    with SessionLocal() as db:
        s = db.scalar(select(Shipment).where(Shipment.order_id == p["order_id"]))
        if s is None or s.status in ("delivered", "cancelled"):
            return
        trip_id = s.trip_id
        s.status = "cancelled"
        db.commit()
        if trip_id:
            _maybe_complete(db, trip_id)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
