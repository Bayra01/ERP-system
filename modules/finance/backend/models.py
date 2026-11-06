<<<<<<< HEAD
import datetime as dt
=======
"""Huvsnegtiin ugtvar: fin_  (nehemjleh, tulbur, zardal)."""
from datetime import date
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.mixins import IdMixin, TimestampMixin


class Invoice(IdMixin, TimestampMixin, Base):
    __tablename__ = "fin_invoices"

    number: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("md_customers.id"), index=True)
<<<<<<< HEAD
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders_orders.id"), unique=True,
                                                 nullable=True)
    issued: Mapped[dt.date] = mapped_column(Date)
    due: Mapped[dt.date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    paid: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
=======
    # order.delivered-ees uussen nehemjleh: 1 zahialga = 1 nehemjleh (unique)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders_orders.id"), unique=True, nullable=True)
    issued: Mapped[date] = mapped_column(Date)
    due: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    paid: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)  # tulburuuden niilber
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), nullable=True)


class Payment(IdMixin, TimestampMixin, Base):
    __tablename__ = "fin_payments"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("fin_invoices.id"), index=True)
<<<<<<< HEAD
    date: Mapped[dt.date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    method: Mapped[str] = mapped_column(String(20), default="bank")  # bank / cash / card
=======
    date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    method: Mapped[str] = mapped_column(String(20))  # transfer | cash | card
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    created_by: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), nullable=True)


class Expense(IdMixin, TimestampMixin, Base):
    __tablename__ = "fin_expenses"

<<<<<<< HEAD
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    vendor: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / paid
=======
    date: Mapped[date] = mapped_column(Date, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    vendor: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    status: Mapped[str] = mapped_column(String(20), default="paid")  # paid | pending
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    created_by: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), nullable=True)
