from sqlalchemy import select
from sqlalchemy.orm import Session

from core.audit import log_action
from core.config import get_settings
from core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from core.permissions import Role
from core.security import create_access_token, hash_password, verify_password

from .models import User
from .schemas import UserCreate, UserUpdate


def authenticate(db: Session, username: str, password: str) -> str:
    user = db.scalar(select(User).where(User.username == username))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Nevtreh ner esvel nuuts ug buruu")
    log_action(db, user.id, "login", "auth.User", user.id)
    return create_access_token(str(user.id), {"role": user.role})


def create_user(db: Session, data: UserCreate, actor_id: int | None = None) -> User:
    if db.scalar(select(User).where(User.username == data.username)):
        raise ConflictError("Ene nertei hereglegch baina")
    user = User(username=data.username, full_name=data.full_name,
                role=data.role.value, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, actor_id, "create", "auth.User", user.id, {"role": user.role})
    return user


def update_user(db: Session, user_id: int, data: UserUpdate, actor_id: int | None = None) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("Hereglegch oldsongui")
    changes = data.model_dump(exclude_unset=True)
    if "password" in changes:
        user.password_hash = hash_password(changes.pop("password"))
    if "role" in changes and changes["role"] is not None:
        user.role = Role(changes.pop("role")).value
    for k, v in changes.items():
        if v is not None:
            setattr(user, k, v)
    db.commit()
    db.refresh(user)
    log_action(db, actor_id, "update", "auth.User", user.id)
    return user


def ensure_first_admin(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)) is not None:
        return
    s = get_settings()
    db.add(User(username=s.FIRST_ADMIN_USERNAME, full_name="Administrator",
                role=Role.ADMIN.value, password_hash=hash_password(s.FIRST_ADMIN_PASSWORD)))
    db.commit()
