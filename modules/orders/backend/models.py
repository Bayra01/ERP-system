"""Hugtsaanii ugtvar: orders_"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from core.mixins import IdMixin, TimestampMixin, utcnow


class Order(IdMixin, TimestampMixin, Base):
    __tablename__ = "orders_orders"

    order_no: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("md_customers.id"), index=True)
    delivery_location_id: Mapped[int | None] = mapped_column(ForeignKey("md_locations.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    requested_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), nullable=True)

    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderLine.id")
    history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderStatusHistory.id")


class OrderLine(IdMixin, Base):
    __tablename__ = "orders_order_lines"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders_orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("md_products.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # zahialgiin uyiin une (snapshot)
    line_total: Mapped[Decimal] = mapped_column(Numeric(16, 2))

    order: Mapped[Order] = relationship(back_populates="lines")


class OrderStatusHistory(IdMixin, Base):
    __tablename__ = "orders_status_history"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders_orders.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    order: Mapped[Order] = relationship(back_populates="history")
