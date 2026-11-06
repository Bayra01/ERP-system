from datetime import date, datetime
<<<<<<< HEAD
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VehicleStatus = Literal["available", "on_trip", "maintenance"]
=======
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class VehicleStatus(str, Enum):
    available = "available"
    maintenance = "maintenance"
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4


class VehicleCreate(BaseModel):
    plate_no: str = Field(min_length=1, max_length=20)
<<<<<<< HEAD
    type: str = Field("truck", max_length=20)
    capacity_kg: float = Field(0, ge=0)
    capacity_m3: float = Field(0, ge=0)
    status: VehicleStatus = "available"
    is_active: bool = True


class VehicleUpdate(BaseModel):
    plate_no: str | None = Field(None, min_length=1, max_length=20)
    type: str | None = Field(None, max_length=20)
    capacity_kg: float | None = Field(None, ge=0)
    capacity_m3: float | None = Field(None, ge=0)
=======
    type: str = Field(default="van", max_length=20)
    capacity_kg: float = Field(default=0, ge=0)
    capacity_m3: float = Field(default=0, ge=0)
    status: VehicleStatus = VehicleStatus.available


class VehicleUpdate(BaseModel):
    type: str | None = Field(default=None, max_length=20)
    capacity_kg: float | None = Field(default=None, ge=0)
    capacity_m3: float | None = Field(default=None, ge=0)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    status: VehicleStatus | None = None
    is_active: bool | None = None


<<<<<<< HEAD
class VehicleOut(BaseModel):
=======
class VehicleRead(BaseModel):
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
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
<<<<<<< HEAD
    phone: str | None = Field(None, max_length=30)
    license_no: str | None = Field(None, max_length=40)
    user_id: int | None = None
    is_active: bool = True


class DriverUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=120)
    phone: str | None = Field(None, max_length=30)
    license_no: str | None = Field(None, max_length=40)
=======
    phone: str | None = None
    license_no: str | None = None
    user_id: int | None = None  # auth_users.id (jolooch role-toi hereglegch)


class DriverUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None
    license_no: str | None = None
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    user_id: int | None = None
    is_active: bool | None = None


<<<<<<< HEAD
class DriverOut(BaseModel):
=======
class DriverRead(BaseModel):
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone: str | None
    license_no: str | None
    user_id: int | None
    is_active: bool


<<<<<<< HEAD
class ShipmentOut(BaseModel):
=======
class ShipmentUpdate(BaseModel):
    location_id: int | None = None
    weight_kg: float | None = Field(default=None, ge=0)
    volume_m3: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=300)


class ShipmentRead(BaseModel):
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
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
<<<<<<< HEAD
    created_at: datetime
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4


class TripCreate(BaseModel):
    vehicle_id: int
    driver_id: int
    planned_date: date
    depot_location_id: int | None = None
    notes: str | None = None
    shipment_ids: list[int] = []


<<<<<<< HEAD
class TripUpdate(BaseModel):
    vehicle_id: int | None = None
    driver_id: int | None = None
    planned_date: date | None = None
    depot_location_id: int | None = None
    notes: str | None = None
    shipment_ids: list[int] | None = None  # ugvul buten soligdono


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trip_no: str | None
    vehicle_id: int
    driver_id: int
    depot_location_id: int | None
    planned_date: date
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_distance_km: float | None
    notes: str | None
    created_at: datetime
    # nemelt (join)
    vehicle_plate: str | None = None
    driver_name: str | None = None
    depot_name: str | None = None
    stops: int = 0
    delivered: int = 0
    weight_kg: float = 0


class TripDetail(TripOut):
    shipments: list[ShipmentOut] = []
=======
class IdsIn(BaseModel):
    shipment_ids: list[int] = Field(min_length=1)


class NoteIn(BaseModel):
    note: str | None = Field(default=None, max_length=300)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4


class FailIn(BaseModel):
    reason: str = Field(min_length=1, max_length=300)


<<<<<<< HEAD
class DeliverIn(BaseModel):
    note: str | None = Field(None, max_length=300)
=======
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
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
