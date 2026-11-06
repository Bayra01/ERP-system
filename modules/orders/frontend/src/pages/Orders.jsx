import { useEffect, useState } from "react";
import { listOrders } from "../api";
import { can } from "../perm";
import { STATUSES, STATUS_LABEL, day, mnt } from "../format";
import Status from "../components/Status";

const SIZE = 20;

export default function Orders({ user, refs }) {
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [customer, setCustomer] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const names = Object.fromEntries(refs.customers.map((c) => [c.id, c.name]));

  useEffect(() => {
    let live = true;
    const t = setTimeout(async () => {
      try {
        const r = await listOrders({ status, q: q.trim(), customer_id: customer, page, size: SIZE });
        if (live) { setData(r); setError(""); }
      } catch (e) {
        if (live) setError(e.message);
      }
    }, q ? 250 : 0);
    return () => { live = false; clearTimeout(t); };
  }, [status, q, customer, page]);

  const reset = (fn) => (v) => { fn(v); setPage(1); };
  const pages = data ? Math.max(1, Math.ceil(data.total / SIZE)) : 1;

  return (
    <>
      <header className="page-head row">
        <div>
          <h1>Захиалгууд</h1>
          <p className="muted">{data ? `Нийт ${data.total} захиалга` : "Ачаалж байна…"}</p>
        </div>
        {can(user.role, "orders:write") && <a className="btn primary" href="#new" style={{ textDecoration: "none" }}>+ Шинэ захиалга</a>}
      </header>

      <div className="toolbar">
        <div className="chips" role="group" aria-label="Төлөвөөр шүүх">
          <button className={`chip ${status === "" ? "on" : ""}`} onClick={() => reset(setStatus)("")}>Бүгд</button>
          {STATUSES.map((s) => (
            <button key={s} className={`chip ${status === s ? "on" : ""}`} onClick={() => reset(setStatus)(s)}>{STATUS_LABEL[s]}</button>
          ))}
        </div>
        <input type="search" placeholder="Захиалгын дугаараар хайх" value={q} onChange={(e) => reset(setQ)(e.target.value)} aria-label="Хайх" />
        <select value={customer} onChange={(e) => reset(setCustomer)(e.target.value)} aria-label="Харилцагч" style={{ width: 220 }}>
          <option value="">Бүх харилцагч</option>
          {refs.customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      {error && <p className="alert" role="alert">{error}</p>}
      <div className="panel flush">
        <div className="scroll">
          <table>
            <thead>
              <tr><th>Дугаар</th><th>Харилцагч</th><th>Төлөв</th><th className="num">Дүн</th><th>Огноо</th><th>Хүргэх огноо</th></tr>
            </thead>
            <tbody>
              {data?.items.map((o) => (
                <tr key={o.id} className="link" tabIndex={0}
                  onClick={() => (location.hash = `#order/${o.id}`)}
                  onKeyDown={(e) => e.key === "Enter" && (location.hash = `#order/${o.id}`)}>
                  <td><a href={`#order/${o.id}`} onClick={(e) => e.stopPropagation()}>{o.order_no || `#${o.id}`}</a></td>
                  <td>{names[o.customer_id] || `#${o.customer_id}`}</td>
                  <td><Status s={o.status} /></td>
                  <td className="num">{mnt(o.total_amount)}</td>
                  <td>{day(o.order_date)}</td>
                  <td>{day(o.requested_delivery_date)}</td>
                </tr>
              ))}
              {data && data.items.length === 0 && <tr><td className="empty" colSpan={6}>Захиалга олдсонгүй</td></tr>}
            </tbody>
          </table>
        </div>
        {data && data.total > SIZE && (
          <div className="pager">
            <span>{page} / {pages} хуудас</span>
            <span className="head-actions">
              <button className="btn small" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Өмнөх</button>
              <button className="btn small" disabled={page >= pages} onClick={() => setPage(page + 1)}>Дараах →</button>
            </span>
          </div>
        )}
      </div>
    </>
  );
}
