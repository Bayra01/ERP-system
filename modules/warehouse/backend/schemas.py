from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

Qty = Field(gt=0, max_digits=14, decimal_places=3)


class ReceiptIn(BaseModel):
    location_id: int
    product_id: int
    quantity: Decimal = Qty
    note: str | None = Field(default=None, max_length=300)


class IssueIn(ReceiptIn):
    """Gar aar zarlaga (hogloh, buruu...). Zahialgiin zarlaga event-eer avtomataar."""


class AdjustIn(BaseModel):
    """Toollogiin zuruu. quantity tamgatai: +5 nemne, -3 hasna."""
    location_id: int
    product_id: int
    quantity: Decimal = Field(max_digits=14, decimal_places=3)
    note: str = Field(min_length=1, max_length=300)

    @field_validator("quantity")
    @classmethod
    def _nonzero(cls, v):
        if v == 0:
            raise ValueError("quantity 0 baij bolohgui")
        return v


class TransferIn(BaseModel):
    from_location_id: int
    to_location_id: int
    product_id: int
    quantity: Decimal = Qty
    note: str | None = Field(default=None, max_length=300)


class MinLevelUpdate(BaseModel):
    min_level: Decimal = Field(ge=0, max_digits=14, decimal_places=3)


class StockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location_id: int
    product_id: int
    on_hand: Decimal
    reserved: Decimal
    min_level: Decimal

    @computed_field
    @property
    def available(self) -> Decimal:
        return self.on_hand - self.reserved


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location_id: int
    product_id: int
    type: str
    quantity: Decimal
    balance_after: Decimal
    ref_type: str | None
    ref_id: int | None
    note: str | None
    user_id: int | None
    created_at: datetime


class ReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    product_id: int
    location_id: int | None
    quantity: Decimal
    status: str


class AvailabilityRead(BaseModel):
    product_id: int
    on_hand: Decimal
    reserved: Decimal
    available: Decimal
