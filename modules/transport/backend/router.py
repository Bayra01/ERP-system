from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permission
from core.pagination import Page, PageParams
from modules.masterdata.backend import service as md

from . import service as svc
from .models import Driver, Vehicle
from .schemas import (DriverCreate, DriverRead, DriverUpdate, FailIn, IdsIn, NoteIn, ShipmentRead,
                      ShipmentUpdate, TripCreate, TripRead, TripSummary, VehicleCreate, VehicleRead,
                      VehicleUpdate)

router = APIRouter(prefix="/api/transport", tags=["Transport"])
read = Depends(require_permission("transport:read"))
write = require_permission("transport:write")
drive = require_permission("transport:drive")


def _page(res, params):
    items, total = res
    return Page(items=items, total=total, page=params.page, size=params.size)


@router.get("/health")
def health():
    return {"module": "transport", "status": "ok"}


# ---------- Vehicles
@router.get("/vehicles", response_model=Page[VehicleRead], dependencies=[read])
def list_vehicles(params: PageParams = Depends(), q: str | None = None, is_active: bool | None = None,
                  db: Session = Depends(get_db)):
    return _page(md.list_items(db, Vehicle, params, q, (Vehicle.plate_no, Vehicle.type), is_active), params)


@router.post("/vehicles", response_model=VehicleRead, status_code=201)
def create_vehicle(body: VehicleCreate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.create_vehicle(db, body, user.id)


@router.get("/vehicles/{vid}", response_model=VehicleRead, dependencies=[read])
def get_vehicle(vid: int, db: Session = Depends(get_db)):
    return md.get_item(db, Vehicle, vid)


@router.patch("/vehicles/{vid}", response_model=VehicleRead)
def update_vehicle(vid: int, body: VehicleUpdate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.update_vehicle(db, vid, body, user.id)


@router.delete("/vehicles/{vid}", status_code=204)
def delete_vehicle(vid: int, db: Session = Depends(get_db), user=Depends(write)):
    svc.delete_vehicle(db, vid, user.id)


# ---------- Drivers
@router.get("/drivers", response_model=Page[DriverRead], dependencies=[read])
def list_drivers(params: PageParams = Depends(), q: str | None = None, is_active: bool | None = None,
                 db: Session = Depends(get_db)):
    return _page(md.list_items(db, Driver, params, q, (Driver.full_name, Driver.phone), is_active), params)


@router.post("/drivers", response_model=DriverRead, status_code=201)
def create_driver(body: DriverCreate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.create_driver(db, body, user.id)


@router.get("/drivers/{did}", response_model=DriverRead, dependencies=[read])
def get_driver(did: int, db: Session = Depends(get_db)):
    return md.get_item(db, Driver, did)


@router.patch("/drivers/{did}", response_model=DriverRead)
def update_driver(did: int, body: DriverUpdate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.update_driver(db, did, body, user.id)


@router.delete("/drivers/{did}", status_code=204)
def delete_driver(did: int, db: Session = Depends(get_db), user=Depends(write)):
    svc.delete_driver(db, did, user.id)


# ---------- Shipments
@router.get("/shipments", response_model=Page[ShipmentRead], dependencies=[read])
def list_shipments(params: PageParams = Depends(), status: str | None = None, ready: bool | None = None,
                   order_id: int | None = None, trip_id: int | None = None, db: Session = Depends(get_db)):
    return _page(svc.list_shipments(db, params, status, ready, order_id, trip_id), params)


@router.get("/shipments/{sid}", response_model=ShipmentRead, dependencies=[read])
def get_shipment(sid: int, db: Session = Depends(get_db)):
    return svc.get_shipment(db, sid)


@router.patch("/shipments/{sid}", response_model=ShipmentRead)
def update_shipment(sid: int, body: ShipmentUpdate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.update_shipment(db, sid, body, user.id)


@router.post("/shipments/{sid}/deliver", response_model=ShipmentRead)
def deliver(sid: int, body: NoteIn | None = None, db: Session = Depends(get_db), user=Depends(drive)):
    return svc.deliver(db, sid, user, body.note if body else None)


@router.post("/shipments/{sid}/fail", response_model=ShipmentRead)
def fail(sid: int, body: FailIn, db: Session = Depends(get_db), user=Depends(drive)):
    return svc.fail(db, sid, user, body.reason)


# ---------- Trips
@router.get("/trips", response_model=Page[TripSummary], dependencies=[read])
def list_trips(params: PageParams = Depends(), status: str | None = None, driver_id: int | None = None,
               vehicle_id: int | None = None, planned_date: date | None = None, db: Session = Depends(get_db)):
    return _page(svc.list_trips(db, params, status, driver_id, vehicle_id, planned_date), params)


@router.get("/my/trips", response_model=Page[TripSummary])
def my_trips(params: PageParams = Depends(), db: Session = Depends(get_db), user=Depends(drive)):
    return _page(svc.my_trips(db, user.id, params), params)


@router.post("/trips", response_model=TripRead, status_code=201)
def create_trip(body: TripCreate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.create_trip(db, body, user.id)


@router.get("/trips/{tid}", response_model=TripRead, dependencies=[read])
def get_trip(tid: int, db: Session = Depends(get_db)):
    return svc.get_trip(db, tid)


@router.post("/trips/{tid}/shipments", response_model=TripRead)
def add_shipments(tid: int, body: IdsIn, db: Session = Depends(get_db), user=Depends(write)):
    return svc.add_shipments(db, tid, body.shipment_ids, user.id)


@router.delete("/trips/{tid}/shipments/{sid}", response_model=TripRead)
def remove_shipment(tid: int, sid: int, db: Session = Depends(get_db), user=Depends(write)):
    return svc.remove_shipment(db, tid, sid, user.id)


@router.put("/trips/{tid}/order", response_model=TripRead)
def reorder(tid: int, body: IdsIn, db: Session = Depends(get_db), user=Depends(write)):
    return svc.reorder(db, tid, body.shipment_ids, user.id)


@router.post("/trips/{tid}/start", response_model=TripRead)
def start_trip(tid: int, db: Session = Depends(get_db), user=Depends(write)):
    return svc.start_trip(db, tid, user.id)


@router.post("/trips/{tid}/cancel", response_model=TripRead)
def cancel_trip(tid: int, db: Session = Depends(get_db), user=Depends(write)):
    return svc.cancel_trip(db, tid, user.id)
