"""FastAPI dependency: odoogiin hereglegch, erh shalgalt.

Ashiglalt (modul router deer):
    from core.deps import require_permission, get_current_user
    @router.post("", dependencies=[Depends(require_permission("orders:write"))])
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from modules.auth.backend.models import User

from .database import get_db
from .exceptions import ForbiddenError, UnauthorizedError
from .permissions import has_permission
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if cred is None:
        raise UnauthorizedError("Token alga")
    try:
        payload = decode_access_token(cred.credentials)
        user_id = int(payload["sub"])
    except Exception:  # noqa: BLE001
        raise UnauthorizedError("Token buruu esvel hugatsaa duussan")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Hereglegch oldsongui esvel idevhgui")
    return user


def require_permission(permission: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role, permission):
            raise ForbiddenError(f"Erh hureltsehgui: {permission}")
        return user
    return checker
