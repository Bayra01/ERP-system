import { useCallback, useEffect, useState } from "react";
import { changeStatus, deleteOrder, getOrder } from "../api";
import { NEXT, TRANSITION_PERM, can } from "../perm";
import { ACTION_LABEL, STATUS_LABEL, day, dayTime, mnt } from "../format";
import Status from "../components/Status";

export default function OrderDetail({ id, user, refs }) {
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try { setOrder(await getOrder(id)); setError(""); } catch (e) { setError(e.message); }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  if (!order) {
    return (
      <>
        <a className="back" href="#orders">← Захиалгууд</a>
        {error ? <p className="alert" role="alert">{error}</p> : <p className="muted">Ачаалж байна…</p>}
      </>
    );
  }

  const customer = refs.customers.find((c) => c.id === order.customer_id)?.name || `#${order.customer_id}`;
  const location_ = refs.locations.find((l) => l.id === order.delivery_location_id);
  const product = (pid) => refs.products.find((p) => p.id === pid);
  const draft = order.status === "draft";
  const canWrite = can(user.role, "orders:write");
  const actions = NEXT[order.status].filter((to) => can(user.role, TRANSITION_PERM[to]));

  const run = async (fn) => {
    setBusy(true); setError("");
    try { await fn(); } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const move = (to) => {
    if (to === "cancelled" && !window.confirm("Захиалгыг цуцлах уу? Нөөц чөлөөлөгдөнө.")) return;
    run(async () => setOrder(await changeStatus(order.id, to)));
  };
  const remove = () => {
    if (!window.confirm("Ноорог захиалгыг устгах уу?")) return;
    run(async () => { await deleteOrder(order.id); location.hash = "#orders"; });
  };

  return (
    <>
      <a className="back" href="#orders">← Захиалгууд</a>
      <header className="page-head row">
        <div>
          <h1>{order.order_no || `Захиалга #${order.id}`} <Status s={order.status} /></h1>
          <p className="muted">{customer}</p>
        </div>
        <div className="head-actions">
          {draft && canWrite && <a className="btn" href={`#edit/${order.id}`} style={{ textDecoration: "none" }}>Засах</a>}
          {draft && canWrite && <button className="btn danger" onClick={remove} disabled={busy}>Устгах</button>}
          {actions.map((to) => (
            <button key={to} className={`btn ${to === "cancelled" ? "danger" : "primary"}`} onClick={() => move(to)} disabled={busy}>
              {ACTION_LABEL[to]}
            </button>
          ))}
        </div>
      </header>

      {error && <p className="alert" role="alert">{error}</p>}

      <section className="panel">
        <dl className="kv">
          <div><dt>Захиалсан огноо</dt><dd>{dayTime(order.order_date)}</dd></div>
          <div><dt>Хүргэх огноо</dt><dd>{day(order.requested_delivery_date)}</dd></div>
          <div><dt>Хүргэх хаяг</dt><dd>{location_ ? location_.name : "—"}</dd></div>
          <div><dt>Нийт дүн</dt><dd>{mnt(order.total_amount)}</dd></div>
          <div><dt>Тэмдэглэл</dt><dd>{order.notes || "—"}</dd></div>
        </dl>
      </section>

      <section className="panel flush">
        <div className="scroll">
          <table>
            <thead><tr><th>Бараа</th><th className="num">Тоо</th><th className="num">Нэгж үнэ</th><th className="num">Дүн</th></tr></thead>
            <tbody>
              {order.lines.map((l) => (
                <tr key={l.id}>
                  <td>{product(l.product_id)?.name || `#${l.product_id}`}</td>
                  <td className="num">{Number(l.quantity)}</td>
                  <td className="num">{mnt(l.unit_price)}</td>
                  <td className="num">{mnt(l.line_total)}</td>
                </tr>
              ))}
              {order.lines.length === 0 && <tr><td className="empty" colSpan={4}>Мөр байхгүй</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Төлвийн түүх</h2>
        <ul className="timeline">
          {order.history.map((h, i) => (
            <li key={i}>
              <i aria-hidden="true" />
              <div>
                {h.from_status ? `${STATUS_LABEL[h.from_status] || h.from_status} → ` : ""}<b>{STATUS_LABEL[h.to_status] || h.to_status}</b>
                <small>{dayTime(h.created_at)}{h.note ? ` · ${h.note}` : ""}</small>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
