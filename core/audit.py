"""Audit log: ken, yu, haana, hezee hiisen."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from .database import Base
from .mixins import IdMixin, utcnow


class AuditLog(IdMixin, Base):
    __tablename__ = "core_audit_logs"

    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(50))       # create/update/delete/login...
    entity: Mapped[str] = mapped_column(String(80), index=True)  # "orders.Order"
    entity_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def log_action(db: Session, user_id: int | None, action: str, entity: str,
               entity_id: int | str | None = None, detail: dict | None = None) -> None:
    db.add(AuditLog(user_id=user_id, action=action, entity=entity,
                    entity_id=None if entity_id is None else str(entity_id), detail=detail))
    db.commit()
