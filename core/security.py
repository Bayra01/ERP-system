"""Nuuts ugiin hash (stdlib PBKDF2) + JWT."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings

_ITER = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITER)
    return f"pbkdf2_sha256${_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        _, it, salt, dk = hashed.split("$")
        new = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(new.hex(), dk)
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, extra: dict | None = None) -> str:
    s = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=s.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": exp, **(extra or {})}
    return jwt.encode(payload, s.SECRET_KEY, algorithm=s.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    s = get_settings()
    return jwt.decode(token, s.SECRET_KEY, algorithms=[s.JWT_ALGORITHM])
