from fastapi import APIRouter, HTTPException  # pyright: ignore[reportMissingImports]

from .schemas import RouteRequest, RouteResponse
from .service import solve

router = APIRouter(prefix="/api/routing", tags=["routing"])


@router.get("/health")
def health():
    return {"module": "routing", "status": "ok"}


@router.post("/optimize", response_model=RouteResponse)
def optimize(req: RouteRequest):
    if req.vehicle_capacity is not None:
        too_big = [s.id for s in req.stops if s.demand > req.vehicle_capacity]
        if too_big:
            raise HTTPException(
                422, f"Машины багтаамжаас их ачаатай зогсоол: {', '.join(too_big)}"
            )
    return solve(req)