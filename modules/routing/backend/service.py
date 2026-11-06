"""Marshrut: haversine zai + nearest-neighbour.

Bairshild lat/lng baihgui zogsoltuud tugsgold (zaig tootsohgui) orno.
"""
import math

from sqlalchemy.orm import Session

from core.exceptions import ConflictError, UnprocessableError
from modules.masterdata.backend.models import Location
from modules.transport.backend import service as transport
from modules.transport.backend.models import Trip

EARTH_KM = 6371.0


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (*a, *b))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2)
    return 2 * EARTH_KM * math.asin(math.sqrt(h))


def _coord(loc: Location | None) -> tuple[float, float] | None:
    if loc is None or loc.lat is None or loc.lng is None:
        return None
    return (loc.lat, loc.lng)


def route_view(db: Session, trip: Trip) -> dict:
    depot = db.get(Location, trip.depot_location_id) if trip.depot_location_id else None
    prev, stops, total = _coord(depot), [], 0.0
    for s in transport.trip_shipments(db, trip.id):
        loc = db.get(Location, s.location_id) if s.location_id else None
        here = _coord(loc)
        leg = round(haversine(prev, here), 2) if prev and here else None
        total += leg or 0
        prev = here or prev
        stops.append({"shipment_id": s.id, "order_id": s.order_id, "sequence": s.stop_sequence,
                      "location_id": s.location_id, "location_name": loc.name if loc else None,
                      "address": loc.address if loc else None, "weight_kg": s.weight_kg,
                      "lat": loc.lat if loc else None, "lng": loc.lng if loc else None,
                      "leg_km": leg, "status": s.status})
    return {"trip_id": trip.id, "trip_no": trip.trip_no, "status": trip.status,
            "depot": {"id": depot.id, "name": depot.name, "lat": depot.lat, "lng": depot.lng}
            if depot else None,
            "stops": stops, "total_distance_km": round(total, 2)}


def _check_planned(trip: Trip) -> None:
    if trip.status != "planned":
        raise ConflictError("Zovhon tuluvluguunii (planned) aylliin marshrutyg uurchilnu")


def _save(db: Session, trip: Trip, ordered: list, previous_km: float) -> dict:
    for i, s in enumerate(ordered, start=1):
        s.stop_sequence = i
    db.flush()
    view = route_view(db, trip)
    trip.total_distance_km = view["total_distance_km"]
    db.commit()
    return {**view, "previous_km": previous_km}


def set_sequence(db: Session, trip: Trip, shipment_ids: list[int]) -> dict:
    """Garaar daraalal: shipment_ids = aylliin buh hurgelt, shine daraallaar."""
    _check_planned(trip)
    shipments = {s.id: s for s in transport.trip_shipments(db, trip.id)}
    if sorted(shipment_ids) != sorted(shipments):
        raise UnprocessableError("shipment_ids ni aylliin buh hurgeltiig yag neg udaa aguulah yostoi")
    previous = route_view(db, trip)["total_distance_km"]
    return _save(db, trip, [shipments[i] for i in shipment_ids], previous)


def optimize(db: Session, trip: Trip) -> dict:
    _check_planned(trip)
    previous = route_view(db, trip)["total_distance_km"]
    shipments = transport.trip_shipments(db, trip.id)
    locs = {s.id: db.get(Location, s.location_id) if s.location_id else None for s in shipments}
    depot = db.get(Location, trip.depot_location_id) if trip.depot_location_id else None
    todo = [s for s in shipments if _coord(locs[s.id])]
    rest = [s for s in shipments if not _coord(locs[s.id])]
    order, cur = [], _coord(depot) or (_coord(locs[todo[0].id]) if todo else None)
    while todo:
        nxt = min(todo, key=lambda s: haversine(cur, _coord(locs[s.id])))
        todo.remove(nxt)
        order.append(nxt)
        cur = _coord(locs[nxt.id])
    return _save(db, trip, order + rest, previous)
