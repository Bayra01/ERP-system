"""/api/notifications - odoogiin hereglegchiin medegdel ba zahidal."""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from core.audit import log_action
from core.database import get_db
from core.deps import get_current_user
from core.exceptions import NotFoundError, UnprocessableError
from core.pagination import Page, PageParams, paginate
from core.permissions import Role
from modules.auth.backend.models import User

from . import handlers  # noqa: F401  event handler burtgene
from .models import Notification

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event: str
    title: str
    message: str | None
    data: dict | None
    is_read: bool
    created_at: datetime
    user_id: int
    sender_id: int | None
    recipient_name: str | None = None
    sender_name: str | None = None


class RecipientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str


class SendIn(BaseModel):
    to_user_id: int | None = None
    role: Role | None = None  # role-iin buh idevhtei hereglegch
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=500)
    reply_to: int | None = None  # hariu bichij bui medegdliin id


def _name(u: User | None) -> str | None:
    return (u.full_name or u.username) if u else None


def _with_names(db: Session, rows: list[Notification]) -> list[dict]:
    ids = {r.user_id for r in rows} | {r.sender_id for r in rows if r.sender_id}
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(ids)))} if ids else {}
    return [{**NotificationOut.model_validate(r).model_dump(),
             "recipient_name": _name(users.get(r.user_id)),
             "sender_name": _name(users.get(r.sender_id))} for r in rows]


@router.get("", response_model=Page[NotificationOut])
def list_notifications(params: PageParams = Depends(), unread: bool = False,
                       box: Literal["inbox", "sent"] = "inbox",
                       kind: Literal["message", "system"] | None = None,
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if box == "sent":
        stmt = select(Notification).where(Notification.sender_id == user.id)
    else:
        stmt = select(Notification).where(Notification.user_id == user.id)
    if unread:
        stmt = stmt.where(Notification.is_read.is_(False))
    if kind == "message":
        stmt = stmt.where(Notification.event == "message")
    elif kind == "system":
        stmt = stmt.where(Notification.event != "message")
    items, total = paginate(db, stmt.order_by(Notification.id.desc()), params)
    return {"items": _with_names(db, items), "total": total, "page": params.page,
            "size": params.size}


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.scalar(select(func.count()).select_from(Notification).where(
        Notification.user_id == user.id, Notification.is_read.is_(False)))
    return {"count": n or 0}


@router.get("/recipients", response_model=list[RecipientOut])
def recipients(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(User).where(User.is_active.is_(True), User.id != user.id)
                      .order_by(User.role, User.full_name)).all()


@router.post("/send", status_code=201)
def send(body: SendIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    to_user_id = body.to_user_id
    if body.reply_to is not None:
        orig = db.get(Notification, body.reply_to)
        if orig is None or orig.user_id != user.id or orig.sender_id is None:
            raise NotFoundError("Hariu bichih zahidal oldsongui")
        to_user_id = orig.sender_id
    if to_user_id is not None:
        u = db.get(User, to_user_id)
        if u is None or not u.is_active:
            raise UnprocessableError("Huleen avagch oldsongui")
        targets, label = [u.id], _name(u)
    elif body.role is not None:
        targets = list(db.scalars(select(User.id).where(
            User.is_active.is_(True), User.role == body.role.value, User.id != user.id)))
        label = f"role:{body.role.value}"
    else:
        raise UnprocessableError("to_user_id, role, reply_to-giin neg n shaardlagatai")
    if not targets:
        raise UnprocessableError("Ene role-d idevhtei hereglegch alga")
    data = {"from_user_id": user.id, "to": label, "reply_to": body.reply_to}
    for uid in targets:
        db.add(Notification(user_id=uid, sender_id=user.id, event="message", title=body.title,
                            message=body.message, data=data))
    db.commit()
    log_action(db, user.id, "send", "notifications.Message", None, {"to": label, "count": len(targets)})
    return {"sent": len(targets)}


@router.post("/read-all", status_code=204)
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(update(Notification).where(Notification.user_id == user.id,
                                          Notification.is_read.is_(False)).values(is_read=True))
    db.commit()


@router.post("/{nid}/read", response_model=NotificationOut)
def read_one(nid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.get(Notification, nid)
    if n is None or n.user_id != user.id:
        raise NotFoundError("Medegdel oldsongui")
    n.is_read = True
    db.commit()
    return _with_names(db, [n])[0]
