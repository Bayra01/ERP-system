from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.mixins import IdMixin, utcnow


class Notification(IdMixin, Base):
    """Hereglegch burt neg mor (event garahad role-oor fan-out hiine).
    event="message" bol hereglegch hoorondiin zahidal (sender_id = ilgeegch)."""
    __tablename__ = "notif_notifications"

    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"), index=True)
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("auth_users.id"), index=True,
                                                  nullable=True)
    event: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
