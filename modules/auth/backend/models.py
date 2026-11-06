from sqlalchemy import Boolean, ForeignKey, String, false
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.mixins import IdMixin, TimestampMixin
from core.permissions import Role


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "auth_users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=Role.DISPATCHER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # /register-eer uuriigee burtguulsen, admin batlaagui (is_active=False). Batalsnii daraa False.
    pending: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # "Hereglegch" (hariltsagch) uuriin hariltsagchtai holbogdono - portal-d zuvhun uuriin zahialga.
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("md_customers.id"), index=True, nullable=True)
