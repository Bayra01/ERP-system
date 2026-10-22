from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CustomerType(str, Enum):
    company = "company"
    individual = "individual"


class LocationType(str, Enum):
    warehouse = "warehouse"
    depot = "depot"
    customer = "customer"
    other = "other"


# ---- Customer
class CustomerBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: CustomerType = CustomerType.company
    register_no: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class CustomerCreate(CustomerBase):
    code: str = Field(min_length=1, max_length=30)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    type: CustomerType | None = None
    register_no: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    is_active: bool | None = None


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    is_active: bool
    created_at: datetime


# ---- Product
class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field(default="pcs", max_length=20)
    weight_kg: float = Field(default=0, ge=0)
    volume_m3: float = Field(default=0, ge=0)
    price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)


class ProductCreate(ProductBase):
    sku: str = Field(min_length=1, max_length=50)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: str | None = Field(default=None, max_length=20)
    weight_kg: float | None = Field(default=None, ge=0)
    volume_m3: float | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    is_active: bool | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    is_active: bool
    created_at: datetime


# ---- Location
class LocationBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: LocationType = LocationType.other
    address: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    customer_id: int | None = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    type: LocationType | None = None
    address: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    customer_id: int | None = None
    is_active: bool | None = None


class LocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: datetime
