import logging
import time
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.config import get_settings
from core.exceptions import ConflictError, TooManyRequestsError, UnauthorizedError
from core.permissions import Role
from core.security import hash_password, verify_password

from .models import User

log = logging.getLogger("erp.auth")


# Nuuts ug taahaas hamgaalna: neg hereglegchiin nereer LOCK_WINDOW dotor MAX_FAILS buruu oroldlogo
# hiivel tur tugjine. Process dotor hadgalna (olon worker bol Redis ruu shiljuulne).
MAX_FAILS, LOCK_WINDOW = 5, 10 * 60
_fails: dict[str, list[float]] = defaultdict(list)


def _recent_fails(key: str) -> list[float]:
    now = time.monotonic()
    _fails[key] = [t for t in _fails[key] if now - t < LOCK_WINDOW]
    return _fails[key]


def authenticate(db: Session, username: str, password: str) -> User:
    key = username.lower()
    fails = _recent_fails(key)
    if len(fails) >= MAX_FAILS:
        wait = int(LOCK_WINDOW - (time.monotonic() - fails[0])) // 60 + 1
        raise TooManyRequestsError(f"Olon udaa buruu oroldson. {wait} minutiin daraa dahin oroldono uu",
                                   retry_minutes=wait)
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        fails.append(time.monotonic())
        raise UnauthorizedError("Hereglegchiin ner esvel nuuts ug buruu",
                                attempts_left=max(0, MAX_FAILS - len(fails)))
    if not user.is_active:
        if user.pending:
            raise UnauthorizedError("Burtgel admin-ii batalgaajuulalt huleej baina", reason="pending")
        raise UnauthorizedError("Hereglegch idevhgui", reason="inactive")
    _fails.pop(key, None)
    return user


# Burtguulehiin spam-aas hamgaalna: neg IP-ees REG_WINDOW dotor REG_MAX huselt.
REG_MAX, REG_WINDOW = 5, 60 * 60
_regs: dict[str, list[float]] = defaultdict(list)


def check_register_rate(ip: str) -> None:
    now = time.monotonic()
    _regs[ip] = [t for t in _regs[ip] if now - t < REG_WINDOW]
    if len(_regs[ip]) >= REG_MAX:
        raise TooManyRequestsError("Olon burtgel ilgeesen. Daraa dahin oroldono uu", retry_minutes=60)
    _regs[ip].append(now)


def create_user(db: Session, username: str, password: str, role: str,
                full_name: str = "", is_active: bool = True, pending: bool = False) -> User:
    if db.scalar(select(User.id).where(User.username == username)):
        raise ConflictError(f"'{username}' hereglegch burtgeltei")
    user = User(username=username, full_name=full_name, role=Role(role).value,
                password_hash=hash_password(password), is_active=is_active, pending=pending)
    db.add(user)
    db.commit()
    return user


def ensure_first_admin(db: Session) -> None:
    """Users table hooson bol .env-iin FIRST_ADMIN-aar admin uusgene."""
    if db.scalar(select(func.count()).select_from(User)):
        return
    s = get_settings()
    create_user(db, s.FIRST_ADMIN_USERNAME, s.FIRST_ADMIN_PASSWORD, Role.ADMIN, "Administrator")
    log.info("first admin created: %s", s.FIRST_ADMIN_USERNAME)
