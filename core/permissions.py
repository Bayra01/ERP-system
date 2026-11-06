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
<<<<<<< HEAD
    USER = "user"  # energiin hereglegch: zuvhun uuriin medeelel, medegdel, messej
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4


# "*" = buh erh
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"*"},
    Role.DISPATCHER: {
        "orders:read", "orders:write", "orders:fulfil", "orders:deliver",
<<<<<<< HEAD
        "transport:read", "transport:write",
=======
        "transport:read", "transport:write", "transport:drive",
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
        "routing:read", "routing:write",
        "warehouse:read", "notifications:read",
        "masterdata:read", "masterdata:write",
    },
<<<<<<< HEAD
    Role.DRIVER: {"transport:read", "routing:read", "orders:read", "orders:deliver",
=======
    Role.DRIVER: {"transport:read", "transport:drive", "routing:read", "orders:read", "orders:deliver",
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
                  "masterdata:read"},
    Role.WAREHOUSE: {"warehouse:read", "warehouse:write", "orders:read", "orders:fulfil",
                     "masterdata:read", "masterdata:write"},
    Role.ACCOUNTANT: {"finance:read", "finance:write", "orders:read", "masterdata:read"},
<<<<<<< HEAD
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


=======
}


>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
def has_permission(role: Role | str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(Role(role), set())
    return "*" in perms or permission in perms
