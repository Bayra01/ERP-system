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
}


def has_permission(role: Role | str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(Role(role), set())
    return "*" in perms or permission in perms
