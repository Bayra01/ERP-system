from datetime import datetime
from decimal import Decimal
<<<<<<< HEAD
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["draft", "confirmed", "picking", "shipped", "delivered", "cancelled"]


class LineIn(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    unit_price: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=2)  # hooson = baraanii une
=======
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
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4


class OrderCreate(BaseModel):
    customer_id: int
    delivery_location_id: int | None = None
    requested_delivery_date: datetime | None = None
    notes: str | None = None
<<<<<<< HEAD
    lines: list[LineIn] = Field(min_length=1)


class OrderUpdate(BaseModel):
=======
    lines: list[OrderLineIn] = Field(min_length=1)


class OrderUpdate(BaseModel):
    """Zuvhun draft tuluvtei zahialga zasna. `lines` ugsun bol buh mor-g solino."""
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    customer_id: int | None = None
    delivery_location_id: int | None = None
    requested_delivery_date: datetime | None = None
    notes: str | None = None
<<<<<<< HEAD
    lines: list[LineIn] | None = Field(None, min_length=1)


class StatusChange(BaseModel):
    to: Status
    note: str | None = Field(None, max_length=300)


class LineOut(BaseModel):
=======
    lines: list[OrderLineIn] | None = Field(default=None, min_length=1)


class StatusChange(BaseModel):
    to: OrderStatus
    note: str | None = Field(default=None, max_length=300)


class OrderLineRead(BaseModel):
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


<<<<<<< HEAD
class HistoryOut(BaseModel):
=======
class HistoryRead(BaseModel):
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    model_config = ConfigDict(from_attributes=True)
    from_status: str | None
    to_status: str
    user_id: int | None
    note: str | None
    created_at: datetime


<<<<<<< HEAD
class OrderOut(BaseModel):
=======
class OrderSummary(BaseModel):
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_no: str | None
    customer_id: int
<<<<<<< HEAD
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
=======
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
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
