import { useMemo, useState } from "react";
import { create } from "../api";
import { invoiceStatus, mnt, STATUS_LABEL, TODAY } from "../format";
import Modal from "../components/Modal";
import Status from "../components/Status";

const iso = (d) => d.toISOString().slice(0, 10);

export default function Invoices({ data, refresh }) {
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const [adding, setAdding] = useState(false);
  const [paying, setPaying] = useState(null);

  const rows = useMemo(
    () => data.invoices
      .map((i) => ({ ...i, status: invoiceStatus(i) }))
      .filter((i) => (filter === "all" || i.status === filter) && (i.customer + i.number).toLowerCase().includes(q.toLowerCase()))
      .sort((a, b) => b.issued.localeCompare(a.issued)),
    [data.invoices, filter, q]
  );
  const total = rows.reduce((s, i) => s + (i.amount - i.paid), 0);

  return (
    <>
      <header className="page-head row">
        <div>
          <h1>Нэхэмжлэх</h1>
          <p className="muted">{rows.length} нэхэмжлэх · үлдэгдэл {mnt(total)}</p>
        </div>
        <button className="btn primary" onClick={() => setAdding(true)}>Нэхэмжлэх үүсгэх</button>
      </header>

      <div className="toolbar">
        <input type="search" placeholder="Харилцагч, дугаараар хайх" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Хайх" />
        <div className="chips" role="group" aria-label="Төлөвөөр шүүх">
          {[["all", "Бүгд"], ...Object.entries(STATUS_LABEL)].map(([k, l]) => (
            <button key={k} className={"chip" + (filter === k ? " on" : "")} aria-pressed={filter === k} onClick={() => setFilter(k)}>{l}</button>
          ))}
        </div>
      </div>

      <section className="panel flush">
        <div className="scroll">
          <table>
            <thead>
              <tr><th>Дугаар</th><th>Харилцагч</th><th>Огноо</th><th>Төлөх хугацаа</th><th className="num">Дүн</th><th className="num">Үлдэгдэл</th><th>Төлөв</th><th /></tr>
            </thead>
            <tbody>
              {rows.map((i) => (
                <tr key={i.id}>
                  <td>{i.number}</td>
                  <td>{i.customer}</td>
                  <td>{i.issued}</td>
                  <td>{i.due}</td>
                  <td className="num">{mnt(i.amount)}</td>
                  <td className="num">{mnt(i.amount - i.paid)}</td>
                  <td><Status s={i.status} /></td>
                  <td className="act" aria-label="Үйлдэл">{i.status !== "paid" && <button className="btn small" onClick={() => setPaying(i)}>Төлбөр</button>}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan="8" className="empty">Шүүлтүүрт тохирох нэхэмжлэх олдсонгүй. Шүүлтүүрээ цэвэрлэж үзнэ үү.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      {adding && <InvoiceForm onClose={() => setAdding(false)} onSaved={() => { setAdding(false); refresh(); }} customers={[...new Set(data.invoices.map((i) => i.customer))]} />}
      {paying && <PaymentForm invoice={paying} onClose={() => setPaying(null)} onSaved={() => { setPaying(null); refresh(); }} />}
    </>
  );
}

function InvoiceForm({ onClose, onSaved, customers }) {
  const due = new Date(TODAY); due.setDate(due.getDate() + 30);
  const [f, setF] = useState({ customer: "", issued: iso(TODAY), due: iso(due), amount: "" });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const valid = f.customer.trim() && Number(f.amount) > 0 && f.due >= f.issued;
  const submit = async (e) => {
    e.preventDefault();
    await create("invoices", { customer: f.customer.trim(), issued: f.issued, due: f.due, amount: Number(f.amount), paid: 0 });
    onSaved();
  };
  return (
    <Modal title="Нэхэмжлэх үүсгэх" onClose={onClose}>
      <form onSubmit={submit}>
        <label>Харилцагч<input list="customers" value={f.customer} onChange={set("customer")} required />
          <datalist id="customers">{customers.map((c) => <option key={c} value={c} />)}</datalist></label>
        <div className="two">
          <label>Огноо<input type="date" value={f.issued} onChange={set("issued")} required /></label>
          <label>Төлөх хугацаа<input type="date" value={f.due} min={f.issued} onChange={set("due")} required /></label>
        </div>
        <label>Дүн (₮)<input type="number" min="1" step="1" value={f.amount} onChange={set("amount")} required /></label>
        <div className="actions"><button type="button" className="btn" onClick={onClose}>Болих</button><button className="btn primary" disabled={!valid}>Нэхэмжлэх үүсгэх</button></div>
      </form>
    </Modal>
  );
}

function PaymentForm({ invoice, onClose, onSaved }) {
  const balance = invoice.amount - invoice.paid;
  const [amount, setAmount] = useState(balance);
  const [method, setMethod] = useState("transfer");
  const [date, setDate] = useState(iso(TODAY));
  const valid = Number(amount) > 0 && Number(amount) <= balance;
  const submit = async (e) => {
    e.preventDefault();
    await create("payments", { invoiceId: invoice.id, date, amount: Number(amount), method });
    onSaved();
  };
  return (
    <Modal title="Төлбөр бүртгэх" onClose={onClose}>
      <form onSubmit={submit}>
        <p className="muted">{invoice.number} · {invoice.customer} · үлдэгдэл {mnt(balance)}</p>
        <label>Дүн (₮)<input type="number" min="1" max={balance} value={amount} onChange={(e) => setAmount(e.target.value)} required />
          {Number(amount) > balance && <span className="err">Дүн үлдэгдлээс ({mnt(balance)}) хэтэрч болохгүй.</span>}</label>
        <div className="two">
          <label>Огноо<input type="date" value={date} onChange={(e) => setDate(e.target.value)} required /></label>
          <label>Төлбөрийн хэлбэр
            <select value={method} onChange={(e) => setMethod(e.target.value)}>
              <option value="transfer">Шилжүүлэг</option><option value="cash">Бэлэн мөнгө</option><option value="card">Карт</option>
            </select></label>
        </div>
        <div className="actions"><button type="button" className="btn" onClick={onClose}>Болих</button><button className="btn primary" disabled={!valid}>Төлбөр бүртгэх</button></div>
      </form>
    </Modal>
  );
}
