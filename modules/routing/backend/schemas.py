from pydantic import BaseModel, Field, model_validator  # pyright: ignore[reportMissingImports]


class Location(BaseModel):
    id: str
    name: str | None = None
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    demand: float = Field(0, ge=0, description="Ачааны хэмжээ (кг, м³ гэх мэт)")


class RouteRequest(BaseModel):
    depot: Location
    stops: list[Location] = Field(min_length=1, max_length=500)
    vehicle_count: int = Field(1, ge=1, le=100)
    vehicle_capacity: float | None = Field(None, gt=0)
    avg_speed_kmh: float = Field(40, gt=0)
    improve: bool = Field(True, description="2-opt сайжруулалт хийх эсэх")

    @model_validator(mode="after")
    def _check(self):
        ids = [self.depot.id] + [s.id for s in self.stops]
        if len(ids) != len(set(ids)):
            raise ValueError("Байршлын id давхцаж болохгүй")
        return self


class VehicleRoute(BaseModel):
    vehicle_index: int
    stop_ids: list[str]
    path: list[Location]
    load: float
    distance_km: float
    duration_min: float


class RouteResponse(BaseModel):
    routes: list[VehicleRoute]
    total_distance_km: float
    total_duration_min: float
    unassigned_stop_ids: list[str]