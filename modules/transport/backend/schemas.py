from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class VehicleStatus(str, Enum):
    available = "available"
    maintenance = "maintenance"


class VehicleCreate(BaseModel):
    plate_no: str = Field(min_length=1, max_length=20)
    type: str = Field(default="van", max_length=20)
    capacity_kg: float = Field(default=0, ge=0)
    capacity_m3: float = Field(default=0, ge=0)
    status: VehicleStatus = VehicleStatus.available


class VehicleUpdate(BaseModel):
    type: str | None = Field(default=None, max_length=20)
    capacity_kg: float | None = Field(default=None, ge=0)
    capacity_m3: float | None = Field(default=None, ge=0)
    status: VehicleStatus | None = None
    is_active: bool | None = None


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plate_no: str
    type: str
    capacity_kg: float
    capacity_m3: float
    status: str
    is_active: bool


class DriverCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    phone: str | None = None
    license_no: str | None = None
    user_id: int | None = None  # auth_users.id (jolooch role-toi hereglegch)


class DriverUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None
    license_no: str | None = None
    user_id: int | None = None
    is_active: bool | None = None


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone: str | None
    license_no: str | None
    user_id: int | None
    is_active: bool


class ShipmentUpdate(BaseModel):
    location_id: int | None = None
    weight_kg: float | None = Field(default=None, ge=0)
    volume_m3: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=300)


class ShipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    customer_id: int | None
    location_id: int | None
    status: str
    ready: bool
    weight_kg: float
    volume_m3: float
    trip_id: int | None
    stop_sequence: int | None
    delivered_at: datetime | None
    failed_reason: str | None
    note: str | None


class TripCreate(BaseModel):
    vehicle_id: int
    driver_id: int
    planned_date: date
    depot_location_id: int | None = None
    notes: str | None = None
    shipment_ids: list[int] = []


class IdsIn(BaseModel):
    shipment_ids: list[int] = Field(min_length=1)


class NoteIn(BaseModel):
    note: str | None = Field(default=None, max_length=300)


class FailIn(BaseModel):
    reason: str = Field(min_length=1, max_length=300)


class TripSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trip_no: str | None
    vehicle_id: int
    driver_id: int
    planned_date: date
    status: str
    started_at: datetime | None
    completed_at: datetime | None


class TripRead(TripSummary):
    depot_location_id: int | None
    notes: str | None
    total_distance_km: float | None
    stops: list[ShipmentRead]

    @computed_field
    @property
    def total_weight_kg(self) -> float:
        return sum(s.weight_kg for s in self.stops if s.status != "cancelled")
