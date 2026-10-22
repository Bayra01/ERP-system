import { dayDiff, invoiceStatus, mnt, mntShort, TODAY } from "../format";

const MONTHS = ["1-р сар","2-р сар","3-р сар","4-р сар","5-р сар","6-р сар","7-р сар","8-р сар","9-р сар","10-р сар","11-р сар","12-р сар"];

export default function Dashboard({ data }) {
  const { invoices, payments, expenses } = data;
  const open = invoices.filter((i) => i.paid < i.amount);
  const bal = (i) => i.amount - i.paid;
  const receivable = open.reduce((s, i) => s + bal(i), 0);

  // Aging buckets by days past due
  const buckets = [
    { key: "current", label: "Хугацаа болоогүй", cls: "b-current", test: (d) => d >= 0 },
    { key: "d30", label: "1–30 хоног", cls: "b-30", test: (d) => d < 0 && d >= -30 },
    { key: "d60", label: "31–60 хоног", cls: "b-60", test: (d) => d < -30 && d >= -60 },
    { key: "d60p", label: "60+ хоног", cls: "b-60p", test: (d) => d < -60 },
  ].map((b) => ({ ...b, sum: open.filter((i) => b.test(dayDiff(i.due))).reduce((s, i) => s + bal(i), 0) }));
  const overdue = buckets.slice(1).reduce((s, b) => s + b.sum, 0);

  // Last 6 months incoming (payments) vs outgoing (expenses)
  const months = Array.from({ length: 6 }, (_, k) => {
    const d = new Date(TODAY.getFullYear(), TODAY.getMonth() - 5 + k, 1);
    return { y: d.getFullYear(), m: d.getMonth(), inc: 0, out: 0 };
  });
  const slot = (iso) => months.find((x) => iso.startsWith(`${x.y}-${String(x.m + 1).padStart(2, "0")}`));
  payments.forEach((p) => { const s = slot(p.date); if (s) s.inc += p.amount; });
  expenses.forEach((e) => { const s = slot(e.date); if (s) s.out += e.amount; });
  const cur = months[5];
  const max = Math.max(1, ...months.flatMap((m) => [m.inc, m.out]));

  const debtors = Object.entries(
    open.reduce((acc, i) => ({ ...acc, [i.customer]: (acc[i.customer] || 0) + bal(i) }), {})
  ).sort((a, b) => b[1] - a[1]).slice(0, 5);

  const recent = [...payments].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 5);
  const byId = Object.fromEntries(invoices.map((i) => [i.id, i]));

  return (
    <>
      <header className="page-head">
        <h1>Санхүүгийн хураангуй</h1>
        <p className="muted">{TODAY.getFullYear()} оны {MONTHS[TODAY.getMonth()]}, {TODAY.getDate()}-ний байдлаар</p>
      </header>

      <section className="panel cargo" aria-labelledby="ar-title">
        <div className="cargo-head">
          <div>
            <h2 id="ar-title">Авлага</h2>
            <p className="big">{mnt(receivable)}</p>
          </div>
          <p className={"overdue-note" + (overdue ? " warn" : "")}>
            {overdue ? <><strong>{mnt(overdue)}</strong> хугацаа хэтэрсэн</> : "Хугацаа хэтэрсэн авлага алга"}
          </p>
        </div>
        <div className="cargo-bar" role="img" aria-label={buckets.map((b) => `${b.label}: ${mnt(b.sum)}`).join(", ")}>
          {buckets.filter((b) => b.sum > 0).map((b) => (
            <span key={b.key} className={b.cls} style={{ flexGrow: b.sum }} title={`${b.label}: ${mnt(b.sum)}`} />
          ))}
        </div>
        <ul className="legend">
          {buckets.map((b) => (
            <li key={b.key}><i className={b.cls} />{b.label}<b>{mnt(b.sum)}</b></li>
          ))}
        </ul>
      </section>

      <section className="kpis">
        <div className="kpi"><span>Энэ сарын орлого</span><b>{mnt(cur.inc)}</b></div>
        <div className="kpi"><span>Энэ сарын зардал</span><b>{mnt(cur.out)}</b></div>
        <div className="kpi"><span>Цэвэр урсгал</span><b className={cur.inc - cur.out < 0 ? "neg" : ""}>{mnt(cur.inc - cur.out)}</b></div>
        <div className="kpi"><span>Нээлттэй нэхэмжлэх</span><b>{open.length}</b></div>
      </section>

      <div className="grid2">
        <section className="panel">
          <h2>Мөнгөн урсгал, сүүлийн 6 сар</h2>
          <svg viewBox="0 0 520 220" className="chart" role="img" aria-label="Орлого ба зардлын сарын харьцуулалт">
            {[0, 0.5, 1].map((t) => (
              <g key={t}>
                <line x1="64" x2="520" y1={180 - t * 150} y2={180 - t * 150} className="grid" />
                <text x="58" y={184 - t * 150} textAnchor="end" className="tick">{t === 0 ? "0" : Math.round((max * t) / 1e6) + " сая"}</text>
              </g>
            ))}
            {months.map((m, k) => {
              const x = 76 + k * 74;
              const h = (v) => (v / max) * 150;
              return (
                <g key={k}>
                  <rect x={x} y={180 - h(m.inc)} width="25" height={h(m.inc)} className="bar-in"><title>Орлого: {mnt(m.inc)}</title></rect>
                  <rect x={x + 28} y={180 - h(m.out)} width="25" height={h(m.out)} className="bar-out"><title>Зардал: {mnt(m.out)}</title></rect>
                  <text x={x + 26} y="202" textAnchor="middle" className="tick">{MONTHS[m.m].replace("-р сар", "")}-р сар</text>
                </g>
              );
            })}
          </svg>
          <ul className="legend inline"><li><i className="b-in" />Орлого</li><li><i className="b-out" />Зардал</li></ul>
        </section>

        <section className="panel">
          <h2>Хамгийн их авлагатай харилцагч</h2>
          {debtors.length === 0 ? <p className="muted">Авлага байхгүй байна.</p> : (
            <ol className="debtors">
              {debtors.map(([name, sum]) => (
                <li key={name}>
                  <span>{name}</span>
                  <b>{mnt(sum)}</b>
                  <em style={{ width: `${(sum / debtors[0][1]) * 100}%` }} />
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>

      <section className="panel">
        <h2>Сүүлийн төлбөрүүд</h2>
        <table>
          <thead><tr><th>Огноо</th><th>Нэхэмжлэх</th><th>Харилцагч</th><th className="num">Дүн</th></tr></thead>
          <tbody>
            {recent.map((p) => (
              <tr key={p.id}>
                <td>{p.date}</td>
                <td>{byId[p.invoiceId]?.number}</td>
                <td>{byId[p.invoiceId]?.customer}</td>
                <td className="num">{mnt(p.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
