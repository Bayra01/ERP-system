from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["draft", "confirmed", "picking", "shipped", "delivered", "cancelled"]


class LineIn(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    unit_price: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=2)  # hooson = baraanii une


class OrderCreate(BaseModel):
    customer_id: int
    delivery_location_id: int | None = None
    requested_delivery_date: datetime | None = None
    notes: str | None = None
    lines: list[LineIn] = Field(min_length=1)


class OrderUpdate(BaseModel):
    customer_id: int | None = None
    delivery_location_id: int | None = None
    requested_delivery_date: datetime | None = None
    notes: str | None = None
    lines: list[LineIn] | None = Field(None, min_length=1)


class StatusChange(BaseModel):
    to: Status
    note: str | None = Field(None, max_length=300)


class LineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    from_status: str | None
    to_status: str
    user_id: int | None
    note: str | None
    created_at: datetime


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_no: str | None
    customer_id: int
    delivery_location_id: int | None
    status: str
    order_date: datetime
    requested_delivery_date: datetime | None
    notes: str | None
    total_amount: Decimal
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class OrderDetail(OrderOut):
    lines: list[LineOut]
    history: list[HistoryOut]
