// core/permissions.py-iin ROLE_PERMISSIONS-iin tsogts. Backend deer uurchlult orovol END mon shinechil.
// Zuvhun menu haruulah/nuuh-d ashiglana; jinhene erhiig backend shalgana.
export const ROLE_LABEL = {
  admin: "Админ",
  dispatcher: "Диспетчер",
  driver: "Жолооч",
  warehouse: "Нярав",
  accountant: "Нягтлан",
};

const ROLE_PERMISSIONS = {
  admin: ["*"],
  dispatcher: [
    "orders:read", "orders:write", "orders:fulfil", "orders:deliver",
    "transport:read", "transport:write", "transport:drive",
    "routing:read", "routing:write",
    "warehouse:read", "notifications:read",
    "masterdata:read", "masterdata:write",
  ],
  driver: ["transport:read", "transport:drive", "routing:read", "orders:read", "orders:deliver", "masterdata:read"],
  warehouse: ["warehouse:read", "warehouse:write", "orders:read", "orders:fulfil", "masterdata:read", "masterdata:write"],
  accountant: ["finance:read", "finance:write", "orders:read", "masterdata:read"],
};

export const hasPermission = (role, permission) => {
  const perms = ROLE_PERMISSIONS[role] || [];
  return perms.includes("*") || perms.includes(permission);
};
