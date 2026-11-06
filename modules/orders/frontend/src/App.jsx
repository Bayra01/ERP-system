import { useCallback, useEffect, useState } from "react";
import { hasToken, logout, lookup, me, onLoggedOut } from "./api";
import { can } from "./perm";
import { ROLE_LABEL } from "./format";
import Orders from "./pages/Orders";
import OrderDetail from "./pages/OrderDetail";
import OrderForm from "./pages/OrderForm";

// Бусад модуль (erp_frontend, FastAPI /erp-ui). /api/auth/me-ийн permissions-оор шүүнэ.
const MODULES = [
  { href: "/erp-ui#db", label: "Хянах самбар", perm: null },
  { href: "/erp-ui#wh", label: "Агуулах", perm: "warehouse:read" },
  { href: "/erp-ui#tr", label: "Тээвэр", perm: "transport:read" },
  { href: "/erp-ui#rt", label: "Маршрут", perm: "routing:read" },
  { href: "/erp-ui#fn", label: "Санхүү", perm: "finance:read" },
  { href: "/erp-ui#md", label: "Мастер өгөгдөл", perm: "masterdata:read" },
  { href: "/erp-ui#nt", label: "Мэдэгдэл", perm: null },
  { href: "/erp-ui#us", label: "Ажилтнууд", perm: "auth:users" },
];
// Нэвтрэлт модулийн /login/orders хуудсаар (FastAPI) явна; дараа нь энд буцаж ирнэ.
const toLogin = (back = true) => location.replace(
  "/login/orders" + (back ? `?next=${encodeURIComponent(location.pathname + location.hash)}` : ""));
const hasPerm = (user, p) => p === null || (user.permissions || []).some((x) => x === "*" || x === p);

// #orders | #new | #order/12 | #edit/12
const parse = () => {
  const [name, id] = location.hash.slice(1).split("/");
  if (name === "new") return { page: "new" };
  if (name === "order" && Number(id)) return { page: "order", id: Number(id) };
  if (name === "edit" && Number(id)) return { page: "edit", id: Number(id) };
  return { page: "orders" };
};

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(hasToken());
  const [route, setRoute] = useState(parse);
  const [refs, setRefs] = useState(null);
  const [error, setError] = useState("");

  const loadSession = useCallback(async () => {
    try {
      const u = await me();
      // Захиалга харах эрхгүй (жишээ: «Хэрэглэгч» үүрэг) бол өөрийн хуудас руу.
      if (!hasPerm(u, "orders:read")) { location.replace("/erp-ui#me"); return; }
      const [customers, products, locations] = await Promise.all([
        lookup("customers"), lookup("products"), lookup("locations"),
      ]);
      setRefs({ customers, products, locations });
      setUser(u);
    } catch (e) {
      // 401 бол api.js token-ийг арилгаад onLoggedOut дуудна; бусад алдааг харуулна (давтан шилжихгүй).
      if (e.status !== 401) setError(e.message);
      setUser(null);
    } finally {
      setBooting(false);
    }
  }, []);

  useEffect(() => { if (hasToken()) loadSession(); else toLogin(); }, [loadSession]);
  useEffect(() => onLoggedOut(() => toLogin(false)), []);
  useEffect(() => {
    const h = () => setRoute(parse());
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);

  if (booting) return <p className="muted" style={{ padding: 24 }}>Ачаалж байна…</p>;
  if (error) return <div className="login-wrap"><div className="panel login"><p className="alert" role="alert">{error}</p><button className="btn" onClick={() => location.reload()}>Дахин оролдох</button></div></div>;
  if (!user || !refs) return <p className="muted" style={{ padding: 24 }}>Нэвтрэх хуудас руу шилжиж байна…</p>;

  const canWrite = can(user.role, "orders:write");
  const nav = [
    { href: "#orders", label: "Захиалгууд", active: route.page !== "new" },
    ...(canWrite ? [{ href: "#new", label: "Шинэ захиалга", active: route.page === "new" }] : []),
  ];

  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <strong>Logistics ERP</strong>
            <span>Захиалга</span>
          </div>
        </div>
        <nav aria-label="Захиалгын цэс">
          {nav.map((n) => (
            <a key={n.href} href={n.href} className={n.active ? "active" : ""} aria-current={n.active ? "page" : undefined}>
              {n.label}
            </a>
          ))}
          <div className="nav-sep" />
          {MODULES.filter((m) => hasPerm(user, m.perm)).map((m) => (
            <a key={m.href} href={m.href}>{m.label}</a>
          ))}
        </nav>
        <div className="side-user">
          <span><b>{user.full_name || user.username}</b><br />{ROLE_LABEL[user.role] || user.role}</span>
          <button className="btn small" onClick={logout}>Гарах</button>
        </div>
      </aside>
      <main className="main">
        {route.page === "orders" && <Orders user={user} refs={refs} />}
        {route.page === "new" && <OrderForm key="new" refs={refs} />}
        {route.page === "edit" && <OrderForm key={`e${route.id}`} id={route.id} refs={refs} />}
        {route.page === "order" && <OrderDetail key={route.id} id={route.id} user={user} refs={refs} />}
      </main>
    </div>
  );
}
