import { lazy } from "react";

// Modul burtgel. Shine modul nemehed: `load` deer modulin component-iig zaaj, `ready: true` bolgono.
// `perm` = menu-d haragdah (read) erh. `pages` = modul dotorh huudasnuud (sub-route).
// Modul component: ({ sub, go }) => JSX   (sub = odoogiin huudas, go(sub) = shiljih)
export const MODULES = [
  {
    id: "orders", label: "Захиалга", perm: "orders:read", prefix: "/api/orders",
    pages: [{ id: "list", label: "Жагсаалт" }],
  },
  {
    id: "warehouse", label: "Агуулах", perm: "warehouse:read", prefix: "/api/warehouse",
    pages: [{ id: "stock", label: "Үлдэгдэл" }],
  },
  {
    id: "transport", label: "Тээвэр", perm: "transport:read", prefix: "/api/transport",
    pages: [{ id: "trips", label: "Аялал" }],
  },
  {
    id: "routing", label: "Маршрут", perm: "routing:read", prefix: "/api/routing",
    pages: [{ id: "plans", label: "Төлөвлөгөө" }],
  },
  {
    id: "finance", label: "Санхүү", perm: "finance:read", prefix: "/api/finance",
    ready: true,
    Component: lazy(() => import("@finance/FinanceModule")),
    pages: [
      { id: "dashboard", label: "Хураангуй" },
      { id: "invoices", label: "Нэхэмжлэх" },
      { id: "payments", label: "Төлбөр" },
      { id: "expenses", label: "Зардал" },
    ],
  },
  {
    id: "masterdata", label: "Үндсэн мэдээлэл", perm: "masterdata:read", prefix: "/api/masterdata",
    pages: [{ id: "customers", label: "Харилцагч" }],
  },
  {
    id: "notifications", label: "Мэдэгдэл", perm: "notifications:read", prefix: "/api/notifications",
    pages: [{ id: "inbox", label: "Ирсэн" }],
  },
];

// Nevtersnii daraa hamgiin ehnii neegdeh modul (role-oos hamaarna).
export const PREFERRED_HOME = ["orders", "transport", "warehouse", "finance", "masterdata", "routing", "notifications"];
