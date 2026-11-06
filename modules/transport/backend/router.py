"""/api/transport - Vehicle, Driver, Shipment, Trip."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from core.audit import log_action
from core.database import get_db
from core.deps import get_current_user, require_permission
from core.exceptions import ConflictError, UnprocessableError
from core.mixins import utcnow
from core.pagination import Page, PageParams, paginate
from core.permissions import Role
from modules.auth.backend.models import User

from . import handlers  # noqa: F401  event handler burtgene
from . import service
from .models import Driver, Shipment, Trip, Vehicle
from .schemas import (DeliverIn, DriverCreate, DriverOut, DriverUpdate, FailIn, ShipmentOut,
                      TripCreate, TripDetail, TripOut, TripUpdate, VehicleCreate, VehicleOut,
                      VehicleUpdate)

router = APIRouter(prefix="/api/transport", tags=["Transport"])
can_read = Depends(require_permission("transport:read"))
can_write = Depends(require_permission("transport:write"))


def _page(items, total, params):
    return {"items": items, "total": total, "page": params.page, "size": params.size}


# ---------------- Vehicles
@router.get("/vehicles", response_model=Page[VehicleOut], dependencies=[can_read])
def list_vehicles(params: PageParams = Depends(), q: str | None = None,
                  status: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Vehicle).where(Vehicle.deleted_at.is_(None))
    if q:
        stmt = stmt.where(Vehicle.plate_no.ilike(f"%{q}%"))
    if status:
        stmt = stmt.where(Vehicle.status == status)
    return _page(*paginate(db, stmt.order_by(Vehicle.id), params), params)


@router.post("/vehicles", response_model=VehicleOut, status_code=201)
def create_vehicle(body: VehicleCreate, db: Session = Depends(get_db), user: User = can_write):
    if db.scalar(select(Vehicle.id).where(Vehicle.plate_no == body.plate_no)):
        raise ConflictError(f"'{body.plate_no}' dugaartai mashin burtgeltei")
    v = Vehicle(**body.model_dump())
    db.add(v)
    db.commit()
    log_action(db, user.id, "create", "transport.Vehicle", v.id)
    return v


@router.patch("/vehicles/{vid}", response_model=VehicleOut)
def update_vehicle(vid: int, body: VehicleUpdate, db: Session = Depends(get_db),
                   user: User = can_write):
    v = service.get_or_404(db, Vehicle, vid, "Mashin")
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    if "plate_no" in data and db.scalar(select(Vehicle.id).where(
            Vehicle.plate_no == data["plate_no"], Vehicle.id != v.id)):
        raise ConflictError(f"'{data['plate_no']}' dugaartai mashin burtgeltei")
    for k, val in data.items():
        setattr(v, k, val)
    db.commit()
    log_action(db, user.id, "update", "transport.Vehicle", v.id, {"fields": sorted(data)})
    return v


@router.delete("/vehicles/{vid}", status_code=204)
def delete_vehicle(vid: int, db: Session = Depends(get_db), user: User = can_write):
    v = service.get_or_404(db, Vehicle, vid, "Mashin")
    if db.scalar(select(Trip.id).where(Trip.vehicle_id == v.id, Trip.status.in_(service.ACTIVE_TRIP))):
        raise ConflictError("Idevhtei aylaltai mashiniig ustgahgui")
    v.deleted_at, v.is_active = utcnow(), False
    db.commit()
    log_action(db, user.id, "delete", "transport.Vehicle", v.id)


# ---------------- Drivers
def _check_driver_user(db: Session, user_id: int | None, exclude: int | None = None):
    if user_id is None:
        return
    u = db.get(User, user_id)
    if u is None or u.role != Role.DRIVER.value:
        raise UnprocessableError("user_id ni driver role-toi hereglegch baih yostoi")
    stmt = select(Driver.id).where(Driver.user_id == user_id)
    if exclude:
        stmt = stmt.where(Driver.id != exclude)
    if db.scalar(stmt):
        raise ConflictError("Ene hereglegch uur joloochid holbogdson")


@router.get("/drivers", response_model=Page[DriverOut], dependencies=[can_read])
def list_drivers(params: PageParams = Depends(), q: str | None = None,
                 db: Session = Depends(get_db)):
    stmt = select(Driver).where(Driver.deleted_at.is_(None))
    if q:
        stmt = stmt.where(or_(Driver.full_name.ilike(f"%{q}%"), Driver.phone.ilike(f"%{q}%")))
    return _page(*paginate(db, stmt.order_by(Driver.id), params), params)


@router.post("/drivers", response_model=DriverOut, status_code=201)
def create_driver(body: DriverCreate, db: Session = Depends(get_db), user: User = can_write):
    _check_driver_user(db, body.user_id)
    d = Driver(**body.model_dump())
    db.add(d)
    db.commit()
    log_action(db, user.id, "create", "transport.Driver", d.id)
    return d


@router.patch("/drivers/{did}", response_model=DriverOut)
def update_driver(did: int, body: DriverUpdate, db: Session = Depends(get_db),
                  user: User = can_write):
    d = service.get_or_404(db, Driver, did, "Jolooch")
    data = body.model_dump(exclude_unset=True)
    if "user_id" in data:
        _check_driver_user(db, data["user_id"], d.id)
    for k, val in data.items():
        if val is not None or k == "user_id":
            setattr(d, k, val)
    db.commit()
    log_action(db, user.id, "update", "transport.Driver", d.id, {"fields": sorted(data)})
    return d


@router.delete("/drivers/{did}", status_code=204)
def delete_driver(did: int, db: Session = Depends(get_db), user: User = can_write):
    d = service.get_or_404(db, Driver, did, "Jolooch")
    if db.scalar(select(Trip.id).where(Trip.driver_id == d.id, Trip.status.in_(service.ACTIVE_TRIP))):
        raise ConflictError("Idevhtei aylaltai joloochiig ustgahgui")
    d.deleted_at, d.is_active, d.user_id = utcnow(), False, None
    db.commit()
    log_action(db, user.id, "delete", "transport.Driver", d.id)


# ---------------- Shipments
@router.get("/shipments", response_model=Page[ShipmentOut], dependencies=[can_read])
def list_shipments(params: PageParams = Depends(), status: str | None = None,
                   ready: bool | None = None, trip_id: int | None = None,
                   unassigned: bool = False, db: Session = Depends(get_db)):
    stmt = select(Shipment)
    if status:
        stmt = stmt.where(Shipment.status.in_(status.split(",")))
    if ready is not None:
        stmt = stmt.where(Shipment.ready.is_(ready))
    if trip_id:
        stmt = stmt.where(Shipment.trip_id == trip_id)
    if unassigned:
        stmt = stmt.where(Shipment.status.in_(service.ASSIGNABLE))
    return _page(*paginate(db, stmt.order_by(Shipment.id.desc()), params), params)


@router.get("/shipments/{sid}", response_model=ShipmentOut, dependencies=[can_read])
def get_shipment(sid: int, db: Session = Depends(get_db)):
    return service.get_or_404(db, Shipment, sid, "Hurgelt")


@router.post("/shipments/{sid}/deliver", response_model=ShipmentOut)
def deliver_shipment(sid: int, body: DeliverIn | None = None, db: Session = Depends(get_db),
                     user: User = can_read):
    sh = service.get_or_404(db, Shipment, sid, "Hurgelt")
    service.deliver(db, sh, user, body.note if body else None)
    log_action(db, user.id, "deliver", "transport.Shipment", sh.id)
    return sh


@router.post("/shipments/{sid}/fail", response_model=ShipmentOut)
def fail_shipment(sid: int, body: FailIn, db: Session = Depends(get_db), user: User = can_read):
    sh = service.get_or_404(db, Shipment, sid, "Hurgelt")
    service.fail(db, sh, user, body.reason)
    log_action(db, user.id, "fail", "transport.Shipment", sh.id, {"reason": body.reason})
    return sh


# ---------------- Trips
def _trip_list(db: Session, stmt, params: PageParams):
    items, total = paginate(db, stmt.order_by(Trip.planned_date.desc(), Trip.id.desc()), params)
    return _page([service.trip_view(db, t) for t in items], total, params)


@router.get("/trips", response_model=Page[TripOut], dependencies=[can_read])
def list_trips(params: PageParams = Depends(), status: str | None = None,
               planned_date: date | None = None, vehicle_id: int | None = None,
               driver_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Trip)
    if status:
        stmt = stmt.where(Trip.status.in_(status.split(",")))
    if planned_date:
        stmt = stmt.where(Trip.planned_date == planned_date)
    if vehicle_id:
        stmt = stmt.where(Trip.vehicle_id == vehicle_id)
    if driver_id:
        stmt = stmt.where(Trip.driver_id == driver_id)
    return _trip_list(db, stmt, params)


@router.get("/my/trips", response_model=Page[TripOut])
def my_trips(params: PageParams = Depends(), db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    stmt = select(Trip).join(Driver, Driver.id == Trip.driver_id).where(Driver.user_id == user.id)
    return _trip_list(db, stmt, params)


@router.get("/trips/{tid}", response_model=TripDetail)
def get_trip(tid: int, db: Session = Depends(get_db), user: User = can_read):
    trip = service.get_or_404(db, Trip, tid, "Aylal")
    if user.role == Role.DRIVER.value:
        service.check_driver_access(db, user, trip)
    return service.trip_view(db, trip, detail=True)


@router.post("/trips", response_model=TripDetail, status_code=201)
def create_trip(body: TripCreate, db: Session = Depends(get_db), user: User = can_write):
    trip = service.create_trip(db, body, user)
    log_action(db, user.id, "create", "transport.Trip", trip.id)
    return service.trip_view(db, trip, detail=True)


@router.patch("/trips/{tid}", response_model=TripDetail)
def update_trip(tid: int, body: TripUpdate, db: Session = Depends(get_db),
                user: User = can_write):
    trip = service.update_trip(db, service.get_or_404(db, Trip, tid, "Aylal"), body)
    log_action(db, user.id, "update", "transport.Trip", trip.id)
    return service.trip_view(db, trip, detail=True)


def _trip_action(name: str, fn):
    def endpoint(tid: int, db: Session = Depends(get_db), user: User = can_write):
        trip = fn(db, service.get_or_404(db, Trip, tid, "Aylal"))
        log_action(db, user.id, name, "transport.Trip", trip.id)
        return service.trip_view(db, trip, detail=True)
    endpoint.__name__ = f"{name}_trip"
    router.post(f"/trips/{{tid}}/{name}", response_model=TripDetail)(endpoint)


_trip_action("start", service.start_trip)
_trip_action("cancel", service.cancel_trip)
_trip_action("complete", service.complete_trip)
