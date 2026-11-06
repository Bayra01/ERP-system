<<<<<<< HEAD
"""/api/auth - main.py deer prefix-tei holbogdono."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import events
from core.audit import AuditLog, log_action
from core.pagination import Page, PageParams, paginate
from core.database import get_db
from core.deps import get_current_user, require_permission
from core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from core.permissions import ROLE_PERMISSIONS, Role, allowed_modules
from core.security import create_access_token, hash_password, verify_password

from . import service
from .models import User
from .schemas import (ApproveIn, AuditOut, LoginIn, MeUpdate, PasswordChange, RegisterIn, TokenOut,
                      UserCreate, UserOut, UserUpdate)

router = APIRouter()
admin_only = Depends(require_permission("auth:users"))  # admin = "*"


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = service.authenticate(db, body.username.strip(), body.password)
    is_admin = user.role == Role.ADMIN.value
    if body.login_as is not None and (body.login_as == "admin") != is_admin:
        log_action(db, user.id, "login_denied", "auth.User", user.id,
                   {"module": body.module, "login_as": body.login_as})
        if is_admin:
            raise ForbiddenError("Admin hereglegch 'Admin' songoltoor nevtrene", reason="use_admin",
                                 role=user.role)
        raise ForbiddenError("Ene hereglegch admin bish", reason="not_admin", role=user.role)
    allowed = allowed_modules(user.role)
    if body.module is not None and body.module not in allowed:
        log_action(db, user.id, "login_denied", "auth.User", user.id, {"module": body.module})
        raise ForbiddenError(f"'{body.module}' modulid erh hureltsehgui", allowed=allowed,
                             role=user.role)
    token = create_access_token(str(user.id), {"role": user.role})
    log_action(db, user.id, "login", "auth.User", user.id,
               {"module": body.module, "login_as": body.login_as})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", status_code=201)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    """Uuriigee burtguuleh: admin batlah hurtel nevtrehgui (is_active=False, pending=True)."""
    service.check_register_rate(request.client.host if request.client else "?")
    user = service.create_user(db, body.username.strip(), body.password, body.role,
                               body.full_name.strip(), is_active=False, pending=True)
    log_action(db, user.id, "register", "auth.User", user.id, {"role": user.role})
    events.publish("user.registered", {"user_id": user.id, "username": user.username,
                                       "full_name": user.full_name, "role": user.role})
    return {"id": user.id, "username": user.username, "pending": True}


@router.get("/me", response_model=UserOut)
=======
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user, require_permission
from core.pagination import Page, PageParams, paginate

from . import service
from .models import User
from .schemas import LoginRequest, TokenResponse, UserCreate, UserRead, UserUpdate

router = APIRouter()
admin_only = require_permission("users:manage")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    return TokenResponse(access_token=service.authenticate(db, body.username, body.password))


@router.get("/me", response_model=UserRead)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
def me(user: User = Depends(get_current_user)):
    return user


<<<<<<< HEAD
@router.patch("/me", response_model=UserOut)
def update_me(body: MeUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Hereglegch uuriin neree zasna (dur, erhiig zuvhun admin)."""
    user.full_name = body.full_name.strip()
    db.commit()
    log_action(db, user.id, "update", "auth.User", user.id, {"fields": ["full_name"]})
    return user


@router.get("/me/activity", response_model=list[AuditOut])
def my_activity(limit: int = 15, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Uuriin suuliin uildluud (nevtrelt, uurchlult) - "Minii medeelel" huudsand."""
    rows = db.scalars(select(AuditLog).where(AuditLog.user_id == user.id)
                      .order_by(AuditLog.id.desc()).limit(max(1, min(limit, 50))))
    return [{**AuditOut.model_validate(r).model_dump(), "user_name": user.full_name or user.username}
            for r in rows]


@router.post("/me/password", status_code=204)
def change_password(body: PasswordChange, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(body.old_password, user.password_hash):
        raise UnprocessableError("Huuchin nuuts ug buruu")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    log_action(db, user.id, "password", "auth.User", user.id)


def _active_admins(db: Session) -> int:
    return len(db.scalars(select(User.id).where(User.role == Role.ADMIN.value,
                                                User.is_active.is_(True))).all())


@router.get("/audit", response_model=Page[AuditOut], dependencies=[admin_only])
def audit_log(params: PageParams = Depends(), user_id: int | None = None,
              entity: str | None = None, action: str | None = None, db: Session = Depends(get_db)):
    """Uildliin tuuh: hen, hezee, yu hiisen (admin)."""
    stmt = select(AuditLog)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if entity:
        stmt = stmt.where(AuditLog.entity.like(f"{entity}%"))
    if action:
        stmt = stmt.where(AuditLog.action == action)
    items, total = paginate(db, stmt.order_by(AuditLog.id.desc()), params)
    names = {u.id: u.full_name or u.username for u in
             db.scalars(select(User).where(User.id.in_({i.user_id for i in items if i.user_id})))}
    return {"items": [{**AuditOut.model_validate(i).model_dump(), "user_name": names.get(i.user_id)}
                      for i in items], "total": total, "page": params.page, "size": params.size}


@router.get("/roles", dependencies=[admin_only])
def list_roles():
    """Dur burt erh ba nevtreh modul (Ajiltnuud huudasnii husnegt)."""
    return [{"role": r.value, "permissions": sorted(ROLE_PERMISSIONS[r]),
             "modules": allowed_modules(r)} for r in Role]


@router.get("/users", response_model=list[UserOut], dependencies=[admin_only])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), actor: User = admin_only):
    user = service.create_user(db, body.username.strip(), body.password, body.role,
                               body.full_name, body.is_active)
    log_action(db, actor.id, "create", "auth.User", user.id)
    return user


def _pending_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Hereglegch oldsongui")
    if not user.pending:
        raise ConflictError("Ene hereglegch burtgeliin huselt bish")
    return user


@router.post("/users/{user_id}/approve", response_model=UserOut)
def approve_user(user_id: int, body: ApproveIn, db: Session = Depends(get_db),
                 actor: User = admin_only):
    user = _pending_user(db, user_id)
    if body.role is not None:
        user.role = Role(body.role).value
    user.is_active, user.pending = True, False
    db.commit()
    log_action(db, actor.id, "approve", "auth.User", user.id, {"role": user.role})
    return user


@router.post("/users/{user_id}/reject", status_code=204)
def reject_user(user_id: int, db: Session = Depends(get_db), actor: User = admin_only):
    """Burtgeliin huseltiig tatgalzana (ustgana). Batlagdsan hereglegchid hamaarahgui."""
    user = _pending_user(db, user_id)
    info = {"username": user.username, "full_name": user.full_name}
    db.delete(user)
    db.commit()
    log_action(db, actor.id, "reject", "auth.User", user_id, info)


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db),
                actor: User = admin_only):
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Hereglegch oldsongui")
    data = body.model_dump(exclude_unset=True)
    demoted = data.get("role") not in (None, Role.ADMIN) or data.get("is_active") is False
    if demoted and user.id == actor.id:
        raise ConflictError("Uuriin admin erh / idevhiig hasah bolomjgui")
    if demoted and user.role == Role.ADMIN.value and _active_admins(db) <= 1:
        raise ConflictError("Suuliin idevhtei adminiig hasah bolomjgui")
    if (pw := data.pop("password", None)) is not None:
        user.password_hash = hash_password(pw)
    if "role" in data and data["role"] is not None:
        data["role"] = data["role"].value
    for k, v in data.items():
        if v is not None:
            setattr(user, k, v)
    db.commit()
    log_action(db, actor.id, "update", "auth.User", user.id, {"fields": sorted(body.model_fields_set)})
    return user
=======
@router.get("/users", response_model=Page[UserRead])
def list_users(params: PageParams = Depends(), db: Session = Depends(get_db),
               _: User = Depends(admin_only)):
    items, total = paginate(db, select(User).order_by(User.id), params)
    return Page(items=items, total=total, page=params.page, size=params.size)


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), actor: User = Depends(admin_only)):
    return service.create_user(db, body, actor.id)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db),
                actor: User = Depends(admin_only)):
    return service.update_user(db, user_id, body, actor.id)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
