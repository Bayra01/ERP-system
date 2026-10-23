import { Suspense, useEffect, useMemo } from "react";
import { useAuth } from "./lib/auth";
import { useRoute } from "./lib/router";
import { MODULES, PREFERRED_HOME } from "./modules";
import Login from "./components/Login";
import Sidebar from "./components/Sidebar";
import Placeholder from "./components/Placeholder";

export default function App() {
  const { user, booting, can, logout } = useAuth();
  const [route, go] = useRoute();

  // Role-d tohirson modulud.
  const allowed = useMemo(() => (user ? MODULES.filter((m) => can(m.perm)) : []), [user, can]);
  const active = allowed.find((m) => m.id === route.module);
  const page = active?.pages.find((p) => p.id === route.sub) || active?.pages[0];

  // Hurdan route / erhgui modul / huudas-gui bol zuv ruu shiljuulne.
  useEffect(() => {
    if (!user || allowed.length === 0) return;
    if (!active) {
      const home = PREFERRED_HOME.map((id) => allowed.find((m) => m.id === id)).find(Boolean) || allowed[0];
      go(home.id, home.pages[0].id, { replace: true });
    } else if (route.sub !== page.id) {
      go(active.id, page.id, { replace: true });
    }
  }, [user, allowed, active, page, route.sub, go]);

  if (booting) return <p className="boot muted">Ачаалж байна…</p>;
  if (!user) return <Login />;

  if (allowed.length === 0) {
    return (
      <main className="login-wrap">
        <div className="login-card">
          <h2>Хандах эрх алга</h2>
          <p className="muted">«{user.username}» хэрэглэгчид нээгдсэн модуль байхгүй байна. Админтай холбогдоно уу.</p>
          <button className="btn" onClick={logout}>Гарах</button>
        </div>
      </main>
    );
  }
  if (!active) return null; // redirect effect ajillaj baina

  const Module = active.Component;
  return (
    <div className="shell">
      <Sidebar modules={allowed} active={active} sub={page.id} user={user} onLogout={logout} />
      <main className="main">
        {Module ? (
          <Suspense fallback={<p className="muted">Ачаалж байна…</p>}>
            <Module sub={page.id} go={(s) => go(active.id, s)} />
          </Suspense>
        ) : (
          <Placeholder module={active} page={page} />
        )}
      </main>
    </div>
  );
}
