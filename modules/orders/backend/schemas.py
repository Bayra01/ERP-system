from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, Enum):
    draft = "draft"
    confirmed = "confirmed"
    picking = "picking"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class OrderLineIn(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    unit_price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)  # hooson bol product.price


class OrderCreate(BaseModel):
    customer_id: int
    delivery_location_id: int | None = None
    requested_delivery_date: datetime | None = None
    notes: str | None = None
    lines: list[OrderLineIn] = Field(min_length=1)


class OrderUpdate(BaseModel):
    """Zuvhun draft tuluvtei zahialga zasna. `lines` ugsun bol buh mor-g solino."""
    customer_id: int | None = None
    delivery_location_id: int | None = None
    requested_delivery_date: datetime | None = None
    notes: str | None = None
    lines: list[OrderLineIn] | None = Field(default=None, min_length=1)


class StatusChange(BaseModel):
    to: OrderStatus
    note: str | None = Field(default=None, max_length=300)


class OrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class HistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    from_status: str | None
    to_status: str
    user_id: int | None
    note: str | None
    created_at: datetime


class OrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_no: str | None
    customer_id: int
    status: str
    total_amount: Decimal
    order_date: datetime
    requested_delivery_date: datetime | None


class OrderRead(OrderSummary):
    delivery_location_id: int | None
    notes: str | None
    created_by: int | None
    lines: list[OrderLineRead]
    history: list[HistoryRead]
