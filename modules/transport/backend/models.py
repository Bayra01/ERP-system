<<<<<<< HEAD
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
=======
"""Hugtsaanii ugtvar: tr_

Shipment = hurgeltiin neg zogsoltsoo (zahialga 1 = shipment 1). Orders-toi FK-gui (order_id zuvhun too).
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4

from core.database import Base
from core.mixins import IdMixin, SoftDeleteMixin, TimestampMixin


class Vehicle(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
<<<<<<< HEAD
    """status: available / on_trip / maintenance"""
    __tablename__ = "tr_vehicles"

    plate_no: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20), default="truck")  # truck / van / car
    capacity_kg: Mapped[float] = mapped_column(Float, default=0)
    capacity_m3: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="available")
=======
    __tablename__ = "tr_vehicles"

    plate_no: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20), default="van")  # van|truck|pickup|other
    capacity_kg: Mapped[float] = mapped_column(Float, default=0.0)  # 0 = hyzgaargui
    capacity_m3: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="available")  # available|maintenance
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Driver(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tr_drivers"

    full_name: Mapped[str] = mapped_column(String(120), index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    license_no: Mapped[str | None] = mapped_column(String(40), nullable=True)
<<<<<<< HEAD
    user_id: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), unique=True,
                                                nullable=True)
=======
    user_id: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), unique=True, nullable=True)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Trip(IdMixin, TimestampMixin, Base):
<<<<<<< HEAD
    """status: planned -> in_progress -> completed, planned -> cancelled"""
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    __tablename__ = "tr_trips"

    trip_no: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("tr_vehicles.id"), index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("tr_drivers.id"), index=True)
<<<<<<< HEAD
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
=======
    depot_location_id: Mapped[int | None] = mapped_column(ForeignKey("md_locations.id"), nullable=True)
    planned_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(12), default="planned", index=True)  # planned|in_progress|completed|cancelled
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)  # routing modul daraa n bugluh
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), nullable=True)

    stops: Mapped[list["Shipment"]] = relationship(back_populates="trip", order_by="Shipment.stop_sequence")


class Shipment(IdMixin, TimestampMixin, Base):
    """status: pending (trip-gui) | assigned (trip-d) | delivered | failed | cancelled"""
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    __tablename__ = "tr_shipments"

    order_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("md_locations.id"), nullable=True)
<<<<<<< HEAD
    status: Mapped[str] = mapped_column(String(12), index=True, default="pending")
    ready: Mapped[bool] = mapped_column(Boolean, default=False)
    weight_kg: Mapped[float] = mapped_column(Float, default=0)
    volume_m3: Mapped[float] = mapped_column(Float, default=0)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("tr_trips.id"), index=True, nullable=True)
=======
    status: Mapped[str] = mapped_column(String(12), default="pending", index=True)
    ready: Mapped[bool] = mapped_column(Boolean, default=False)  # order.shipped (achaalt duusaj aguulahaas garsan)
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    volume_m3: Mapped[float] = mapped_column(Float, default=0.0)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("tr_trips.id"), nullable=True, index=True)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    stop_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
<<<<<<< HEAD
=======

    trip: Mapped[Trip | None] = relationship(back_populates="stops")
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
