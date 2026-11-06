"""Role + permission. Modul bolgon uuriin permission-oo END nemne.

Permission format: "<modul>:<uildel>"  jishee: "orders:write"
"""
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    DRIVER = "driver"
    WAREHOUSE = "warehouse"
    ACCOUNTANT = "accountant"
    USER = "user"  # energiin hereglegch: zuvhun uuriin medeelel, medegdel, messej


# "*" = buh erh
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"*"},
    Role.DISPATCHER: {
        "orders:read", "orders:write", "orders:fulfil", "orders:deliver",
        "transport:read", "transport:write",
        "routing:read", "routing:write",
        "warehouse:read", "notifications:read",
        "masterdata:read", "masterdata:write",
    },
    Role.DRIVER: {"transport:read", "routing:read", "orders:read", "orders:deliver",
                  "masterdata:read"},
    Role.WAREHOUSE: {"warehouse:read", "warehouse:write", "orders:read", "orders:fulfil",
                     "masterdata:read", "masterdata:write"},
    Role.ACCOUNTANT: {"finance:read", "finance:write", "orders:read", "masterdata:read"},
    Role.USER: {"notifications:read", "portal:use"},
}


# Modul burt nevtreh erh (/login/<modul>). None = buh hereglegch.
MODULE_PERMISSIONS: dict[str, str | None] = {
    "orders": "orders:read",
    "warehouse": "warehouse:read",
    "transport": "transport:read",
    "routing": "routing:read",
    "finance": "finance:read",
    "notifications": None,
}


def allowed_modules(role: Role | str) -> list[str]:
    return [m for m, p in MODULE_PERMISSIONS.items() if p is None or has_permission(role, p)]


def has_permission(role: Role | str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(Role(role), set())
    return "*" in perms or permission in perms
