import { ROLE_LABEL } from "../lib/permissions";

export default function Sidebar({ modules, active, sub, user, onLogout }) {
  return (
    <aside className="side">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true" />
        <div><strong>Logistics ERP</strong><span>{active?.label}</span></div>
      </div>

      <nav aria-label="Модулиуд">
        {modules.map((m) => (
          <div key={m.id} className="nav-group">
            <a href={`#/${m.id}`} className={m.id === active?.id ? "active" : ""} aria-current={m.id === active?.id ? "page" : undefined}>
              {m.label}
            </a>
            {m.id === active?.id && m.pages.length > 1 && (
              <div className="subnav" role="group" aria-label={`${m.label} хуудсууд`}>
                {m.pages.map((p) => (
                  <a key={p.id} href={`#/${m.id}/${p.id}`} className={p.id === sub ? "active" : ""} aria-current={p.id === sub ? "page" : undefined}>
                    {p.label}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      <div className="userbox">
        <div>
          <strong>{user.full_name || user.username}</strong>
          <span>{ROLE_LABEL[user.role] || user.role}</span>
        </div>
        <button className="btn small" onClick={onLogout}>Гарах</button>
      </div>
    </aside>
  );
}
