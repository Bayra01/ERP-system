"""/api/routing"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.audit import log_action
from core.database import get_db
from core.deps import require_permission
from modules.auth.backend.models import User
from modules.masterdata.backend.models import Location
from modules.transport.backend import service as transport
from modules.transport.backend.models import Trip

from . import service

router = APIRouter(prefix="/api/routing", tags=["Routing"])
can_read = Depends(require_permission("routing:read"))
can_write = Depends(require_permission("routing:write"))


@router.get("/trips/{trip_id}", dependencies=[can_read])
def get_route(trip_id: int, db: Session = Depends(get_db)):
    return service.route_view(db, transport.get_or_404(db, Trip, trip_id, "Aylal"))


@router.post("/trips/{trip_id}/optimize")
def optimize(trip_id: int, db: Session = Depends(get_db), user: User = can_write):
    view = service.optimize(db, transport.get_or_404(db, Trip, trip_id, "Aylal"))
    log_action(db, user.id, "optimize", "routing.Trip", trip_id,
               {"total_distance_km": view["total_distance_km"]})
    return view


class SequenceIn(BaseModel):
    shipment_ids: list[int]


@router.put("/trips/{trip_id}/sequence")
def set_sequence(trip_id: int, body: SequenceIn, db: Session = Depends(get_db),
                 user: User = can_write):
    view = service.set_sequence(db, transport.get_or_404(db, Trip, trip_id, "Aylal"),
                                body.shipment_ids)
    log_action(db, user.id, "sequence", "routing.Trip", trip_id,
               {"total_distance_km": view["total_distance_km"]})
    return view


@router.get("/distance", dependencies=[can_read])
def distance(from_id: int, to_id: int, db: Session = Depends(get_db)):
    a = transport.get_or_404(db, Location, from_id, "Bairshil")
    b = transport.get_or_404(db, Location, to_id, "Bairshil")
    ca, cb = service._coord(a), service._coord(b)
    return {"from_id": a.id, "to_id": b.id,
            "km": round(service.haversine(ca, cb), 2) if ca and cb else None}
