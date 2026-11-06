from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VehicleStatus = Literal["available", "on_trip", "maintenance"]


class VehicleCreate(BaseModel):
    plate_no: str = Field(min_length=1, max_length=20)
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
    status: VehicleStatus | None = None
    is_active: bool | None = None


class VehicleOut(BaseModel):
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
    phone: str | None = Field(None, max_length=30)
    license_no: str | None = Field(None, max_length=40)
    user_id: int | None = None
    is_active: bool = True


class DriverUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=120)
    phone: str | None = Field(None, max_length=30)
    license_no: str | None = Field(None, max_length=40)
    user_id: int | None = None
    is_active: bool | None = None


class DriverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone: str | None
    license_no: str | None
    user_id: int | None
    is_active: bool


class ShipmentOut(BaseModel):
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
    created_at: datetime


class TripCreate(BaseModel):
    vehicle_id: int
    driver_id: int
    planned_date: date
    depot_location_id: int | None = None
    notes: str | None = None
    shipment_ids: list[int] = []


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


class FailIn(BaseModel):
    reason: str = Field(min_length=1, max_length=300)


class DeliverIn(BaseModel):
    note: str | None = Field(None, max_length=300)
