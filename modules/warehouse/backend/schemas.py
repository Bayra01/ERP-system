from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MovementIn(BaseModel):
    location_id: int
    product_id: int
    type: Literal["in", "out", "adjust"]
    quantity: Decimal = Field(ge=0, max_digits=14, decimal_places=3)
    note: str | None = Field(None, max_length=300)


class TransferIn(BaseModel):
    from_location_id: int
    to_location_id: int
    product_id: int
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    note: str | None = Field(None, max_length=300)


class StockUpdate(BaseModel):
    min_level: Decimal = Field(ge=0, max_digits=14, decimal_places=3)


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    address: str | None


class StockOut(BaseModel):
    id: int
    location_id: int
    location_name: str
    product_id: int
    sku: str
    product_name: str
    unit: str
    on_hand: float
    reserved: float
    available: float
    min_level: float
    status: Literal["ok", "low", "out"]
    updated_at: datetime


class MovementOut(BaseModel):
    id: int
    location_id: int
    location_name: str
    product_id: int
    sku: str
    product_name: str
    type: str
    quantity: float
    balance_after: float
    ref_type: str | None
    ref_id: int | None
    note: str | None
    user_id: int | None
    created_at: datetime


class ReservationOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    location_id: int | None
    quantity: float
    status: str


class Summary(BaseModel):
    products: int
    total_on_hand: float
    total_reserved: float
    low: int
    out: int
