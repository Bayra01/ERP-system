"""Hugtsaanii ugtvar: md_  (Customers, Products, Locations)"""
from decimal import Decimal

from sqlalchemy import Boolean, Float, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.mixins import IdMixin, SoftDeleteMixin, TimestampMixin


class Customer(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "md_customers"

    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    type: Mapped[str] = mapped_column(String(20), default="company")  # company | individual
    register_no: Mapped[str | None] = mapped_column(String(30), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "md_products"

    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    unit: Mapped[str] = mapped_column(String(20), default="pcs")  # pcs, kg, box, pallet ...
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    volume_m3: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Location(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Hayag/tsegt: aguulah, depot, hariltsagchiin hayag. lat/lng -> routing ashiglana."""
    __tablename__ = "md_locations"

    name: Mapped[str] = mapped_column(String(200), index=True)
    type: Mapped[str] = mapped_column(String(20), default="other")  # warehouse|depot|customer|other
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("md_customers.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
