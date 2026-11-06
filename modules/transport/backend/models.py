from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.mixins import IdMixin, SoftDeleteMixin, TimestampMixin


class Vehicle(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    """status: available / on_trip / maintenance"""
    __tablename__ = "tr_vehicles"

    plate_no: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20), default="truck")  # truck / van / car
    capacity_kg: Mapped[float] = mapped_column(Float, default=0)
    capacity_m3: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="available")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Driver(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tr_drivers"

    full_name: Mapped[str] = mapped_column(String(120), index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    license_no: Mapped[str | None] = mapped_column(String(40), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), unique=True,
                                                nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Trip(IdMixin, TimestampMixin, Base):
    """status: planned -> in_progress -> completed, planned -> cancelled"""
    __tablename__ = "tr_trips"

    trip_no: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("tr_vehicles.id"), index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("tr_drivers.id"), index=True)
    depot_location_id: Mapped[int | None] = mapped_column(ForeignKey("md_locations.id"),
                                                          nullable=True)
    planned_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(12), index=True, default="planned")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), nullable=True)


class Shipment(IdMixin, TimestampMixin, Base):
    """Zahialga burt 1 hurgelt. status: pending / assigned / in_transit / delivered / failed / cancelled"""
    __tablename__ = "tr_shipments"

    order_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("md_locations.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(12), index=True, default="pending")
    ready: Mapped[bool] = mapped_column(Boolean, default=False)
    weight_kg: Mapped[float] = mapped_column(Float, default=0)
    volume_m3: Mapped[float] = mapped_column(Float, default=0)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("tr_trips.id"), index=True, nullable=True)
    stop_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
