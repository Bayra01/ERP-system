// Mirrors core/permissions.py (orders:* only). The backend still enforces everything;
// this only decides which buttons to show.
const ORDERS_PERMS = {
  admin: ["*"],
  dispatcher: ["orders:read", "orders:write", "orders:fulfil", "orders:deliver"],
  driver: ["orders:read", "orders:deliver"],
  warehouse: ["orders:read", "orders:fulfil"],
  accountant: ["orders:read"],
};

export const can = (role, perm) => {
  const p = ORDERS_PERMS[role] || [];
  return p.includes("*") || p.includes(perm);
};

// services.py: ALLOWED / TRANSITION_PERMISSION
export const NEXT = {
  draft: ["confirmed", "cancelled"],
  confirmed: ["picking", "cancelled"],
  picking: ["shipped", "cancelled"],
  shipped: ["delivered"],
  delivered: [],
  cancelled: [],
};
export const TRANSITION_PERM = {
  confirmed: "orders:write",
  cancelled: "orders:write",
  picking: "orders:fulfil",
  shipped: "orders:fulfil",
  delivered: "orders:deliver",
};
