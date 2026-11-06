import { useMemo, useState } from "react";
import { create } from "../api";
import { EXPENSE_CATEGORIES, mnt, TODAY } from "../format";
import Modal from "../components/Modal";

export default function Expenses({ data, refresh }) {
  const [cat, setCat] = useState("all");
  const [adding, setAdding] = useState(false);
  const rows = useMemo(
    () => data.expenses.filter((e) => cat === "all" || e.category === cat).sort((a, b) => b.date.localeCompare(a.date)),
    [data.expenses, cat]
  );
  const total = rows.reduce((s, e) => s + e.amount, 0);
  const byCat = EXPENSE_CATEGORIES.map((c) => [c, data.expenses.filter((e) => e.category === c).reduce((s, e) => s + e.amount, 0)])
    .filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]);
  const all = byCat.reduce((s, [, v]) => s + v, 0) || 1;

  return (
    <>
      <header className="page-head row">
        <div>
          <h1>Зардал</h1>
          <p className="muted">{rows.length} бичилт · нийт {mnt(total)}</p>
        </div>
        <button className="btn primary" onClick={() => setAdding(true)}>Зардал нэмэх</button>
      </header>

      <section className="panel">
        <h2>Ангиллаар</h2>
        <div className="cargo-bar slim" role="img" aria-label="Зардлын ангилал">
          {byCat.map(([c, v], k) => <span key={c} className={"cat-" + (k % 6)} style={{ flexGrow: v }} title={`${c}: ${mnt(v)}`} />)}
        </div>
        <ul className="legend">
          {byCat.map(([c, v], k) => <li key={c}><i className={"cat-" + (k % 6)} />{c}<b>{Math.round((v / all) * 100)}%</b></li>)}
        </ul>
      </section>

      <div className="toolbar">
        <div className="chips" role="group" aria-label="Ангиллаар шүүх">
          {["all", ...EXPENSE_CATEGORIES].map((c) => (
            <button key={c} className={"chip" + (cat === c ? " on" : "")} aria-pressed={cat === c} onClick={() => setCat(c)}>{c === "all" ? "Бүгд" : c}</button>
          ))}
        </div>
      </div>

      <section className="panel flush">
        <div className="scroll">
          <table>
            <thead><tr><th>Огноо</th><th>Ангилал</th><th>Нийлүүлэгч</th><th>Төлөв</th><th className="num">Дүн</th></tr></thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id}>
                  <td>{e.date}</td><td>{e.category}</td><td>{e.vendor}</td>
                  <td><span className={"pill " + (e.status === "paid" ? "paid" : "open")}>{e.status === "paid" ? "Төлөгдсөн" : "Хүлээгдэж буй"}</span></td>
                  <td className="num">{mnt(e.amount)}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan="5" className="empty">Энэ ангилалд зардал бүртгэгдээгүй байна.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
      {adding && <ExpenseForm onClose={() => setAdding(false)} onSaved={() => { setAdding(false); refresh(); }} />}
    </>
  );
}

function ExpenseForm({ onClose, onSaved }) {
  const [f, setF] = useState({ date: TODAY.toISOString().slice(0, 10), category: EXPENSE_CATEGORIES[0], vendor: "", amount: "", status: "paid" });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const valid = f.vendor.trim() && Number(f.amount) > 0;
  const submit = async (e) => {
    e.preventDefault();
    await create("expenses", { ...f, vendor: f.vendor.trim(), amount: Number(f.amount) });
    onSaved();
  };
  return (
    <Modal title="Зардал нэмэх" onClose={onClose}>
      <form onSubmit={submit}>
        <div className="two">
          <label>Огноо<input type="date" value={f.date} onChange={set("date")} required /></label>
          <label>Ангилал<select value={f.category} onChange={set("category")}>{EXPENSE_CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></label>
        </div>
        <label>Нийлүүлэгч<input value={f.vendor} onChange={set("vendor")} required /></label>
        <div className="two">
          <label>Дүн (₮)<input type="number" min="1" value={f.amount} onChange={set("amount")} required /></label>
          <label>Төлөв<select value={f.status} onChange={set("status")}><option value="paid">Төлөгдсөн</option><option value="pending">Хүлээгдэж буй</option></select></label>
        </div>
        <div className="actions"><button type="button" className="btn" onClick={onClose}>Болих</button><button className="btn primary" disabled={!valid}>Зардал нэмэх</button></div>
      </form>
    </Modal>
  );
}
