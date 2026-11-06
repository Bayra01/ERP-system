from datetime import datetime
from decimal import Decimal
<<<<<<< HEAD
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LocationType = Literal["warehouse", "customer", "depot"]


class _Out(BaseModel):
=======
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
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: datetime
<<<<<<< HEAD
    updated_at: datetime


# --- Customer
class CustomerCreate(BaseModel):
    code: str | None = Field(None, max_length=30)  # hooson bol C-<id>
    name: str = Field(min_length=1, max_length=200)
    type: Literal["company", "individual"] = "company"
    register_no: str | None = Field(None, max_length=30)
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=120)
    address: str | None = Field(None, max_length=300)
    is_active: bool = True


class CustomerUpdate(BaseModel):
    code: str | None = Field(None, max_length=30)
    name: str | None = Field(None, min_length=1, max_length=200)
    type: Literal["company", "individual"] | None = None
    register_no: str | None = Field(None, max_length=30)
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=120)
    address: str | None = Field(None, max_length=300)
    is_active: bool | None = None


class CustomerOut(_Out):
    code: str
    name: str
    type: str
    register_no: str | None
    phone: str | None
    email: str | None
    address: str | None


# --- Product
class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field("pcs", max_length=20)
    weight_kg: float = Field(0, ge=0)
    volume_m3: float = Field(0, ge=0)
    price: Decimal = Field(Decimal(0), ge=0, max_digits=14, decimal_places=2)
    is_active: bool = True


class ProductUpdate(BaseModel):
    sku: str | None = Field(None, min_length=1, max_length=50)
    name: str | None = Field(None, min_length=1, max_length=200)
    unit: str | None = Field(None, max_length=20)
    weight_kg: float | None = Field(None, ge=0)
    volume_m3: float | None = Field(None, ge=0)
    price: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=2)
    is_active: bool | None = None


class ProductOut(_Out):
    sku: str
    name: str
    unit: str
    weight_kg: float
    volume_m3: float
    price: Decimal


# --- Location
class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: LocationType = "customer"
    address: str | None = Field(None, max_length=300)
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)
    customer_id: int | None = None
    is_active: bool = True


class LocationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    type: LocationType | None = None
    address: str | None = Field(None, max_length=300)
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)
    customer_id: int | None = None
    is_active: bool | None = None


class LocationOut(_Out):
    name: str
    type: str
    address: str | None
    lat: float | None
    lng: float | None
    customer_id: int | None
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
