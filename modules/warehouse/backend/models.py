from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.mixins import IdMixin, TimestampMixin, utcnow


class Stock(IdMixin, TimestampMixin, Base):
    """Aguulah (md_locations type=warehouse) x baraa burt neg mor."""
    __tablename__ = "wh_stock"
    __table_args__ = (UniqueConstraint("location_id", "product_id", name="uq_wh_stock_loc_prod"),)

    location_id: Mapped[int] = mapped_column(ForeignKey("md_locations.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("md_products.id"), index=True)
    on_hand: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    reserved: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    min_level: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)

    @property
    def available(self) -> Decimal:
        return Decimal(self.on_hand or 0) - Decimal(self.reserved or 0)


class Movement(IdMixin, Base):
    """Ledger. quantity = temdegtei uurchlult (out < 0)."""
    __tablename__ = "wh_movements"

    location_id: Mapped[int] = mapped_column(ForeignKey("md_locations.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("md_products.id"), index=True)
    type: Mapped[str] = mapped_column(String(20), index=True)  # in/out/adjust/transfer_in/transfer_out
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    ref_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # order / transfer
    ref_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Reservation(IdMixin, TimestampMixin, Base):
    """status: reserved / short / released / consumed"""
    __tablename__ = "wh_reservations"

    order_id: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("md_products.id"), index=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("md_locations.id"), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    status: Mapped[str] = mapped_column(String(12), index=True, default="reserved")
