import { useEffect, useState } from "react";
import { createOrder, getOrder, updateOrder } from "../api";
import { mnt } from "../format";

let seq = 0;
const blankLine = () => ({ key: ++seq, productId: "", quantity: "1", unitPrice: "" });

export default function OrderForm({ id, refs }) {
  const editing = Boolean(id);
  const [f, setF] = useState({ customerId: "", locationId: "", date: "", notes: "" });
  const [lines, setLines] = useState([blankLine()]);
  const [loading, setLoading] = useState(editing);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!editing) return;
    getOrder(id).then((o) => {
      if (o.status !== "draft") { setError("Зөвхөн ноорог захиалгыг засах боломжтой"); return; }
      setF({
        customerId: String(o.customer_id),
        locationId: o.delivery_location_id ? String(o.delivery_location_id) : "",
        date: o.requested_delivery_date ? o.requested_delivery_date.slice(0, 10) : "",
        notes: o.notes || "",
      });
      setLines(o.lines.map((l) => ({ key: ++seq, productId: String(l.product_id), quantity: String(Number(l.quantity)), unitPrice: String(Number(l.unit_price)) })));
    }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [editing, id]);

  const cid = Number(f.customerId);
  const places = refs.locations.filter((l) => l.is_active !== false &&
    (l.customer_id === cid || (l.customer_id == null && l.type !== "warehouse")));
  const price = (l) => {
    if (l.unitPrice !== "") return Number(l.unitPrice) || 0;
    return Number(refs.products.find((p) => p.id === Number(l.productId))?.price) || 0;
  };
  const total = lines.reduce((s, l) => s + (Number(l.quantity) || 0) * price(l), 0);

  const setLine = (key, patch) => setLines(lines.map((l) => (l.key === key ? { ...l, ...patch } : l)));
  const valid = f.customerId && lines.length > 0 && lines.every((l) => l.productId && Number(l.quantity) > 0);

  const submit = async (e) => {
    e.preventDefault();
    if (!valid) return;
    const body = {
      customer_id: cid,
      delivery_location_id: f.locationId ? Number(f.locationId) : null,
      requested_delivery_date: f.date ? `${f.date}T00:00:00` : null,
      notes: f.notes.trim() || null,
      lines: lines.map((l) => ({
        product_id: Number(l.productId),
        quantity: String(l.quantity),
        ...(l.unitPrice !== "" ? { unit_price: String(l.unitPrice) } : {}),
      })),
    };
    setBusy(true); setError("");
    try {
      const saved = editing ? await updateOrder(id, body) : await createOrder(body);
      location.hash = `#order/${saved.id}`;
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  if (loading) return <p className="muted">Ачаалж байна…</p>;

  return (
    <>
      <a className="back" href={editing ? `#order/${id}` : "#orders"}>← Буцах</a>
      <header className="page-head"><h1>{editing ? "Захиалга засах" : "Шинэ захиалга"}</h1></header>
      <form onSubmit={submit}>
        <section className="panel">
          <div className="form-grid">
            <label className="field">Харилцагч
              <select value={f.customerId} onChange={(e) => setF({ ...f, customerId: e.target.value, locationId: "" })} required>
                <option value="">Сонгох…</option>
                {refs.customers.filter((c) => c.is_active !== false).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </label>
            <label className="field">Хүргэх хаяг
              <select value={f.locationId} onChange={(e) => setF({ ...f, locationId: e.target.value })} disabled={!f.customerId}>
                <option value="">— сонгоогүй —</option>
                {places.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </label>
            <label className="field">Хүргэх огноо
              <input type="date" value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} />
            </label>
          </div>
          <label className="field" style={{ marginTop: 14 }}>Тэмдэглэл
            <input value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} />
          </label>
        </section>

        <section className="panel">
          <h2>Барааны мөр</h2>
          <div className="scroll">
            <table className="lines">
              <thead><tr><th>Бараа</th><th>Тоо</th><th>Нэгж үнэ (хоосон бол бүтээгдэхүүний үнэ)</th><th className="num">Дүн</th><th /></tr></thead>
              <tbody>
                {lines.map((l) => (
                  <tr key={l.key}>
                    <td>
                      <select value={l.productId} onChange={(e) => setLine(l.key, { productId: e.target.value })} aria-label="Бараа" required>
                        <option value="">Сонгох…</option>
                        {refs.products.filter((p) => p.is_active !== false).map((p) => <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>)}
                      </select>
                    </td>
                    <td><input type="number" min="0.001" step="any" value={l.quantity} onChange={(e) => setLine(l.key, { quantity: e.target.value })} aria-label="Тоо" required /></td>
                    <td>
                      <input type="number" min="0" step="any" value={l.unitPrice} aria-label="Нэгж үнэ"
                        placeholder={l.productId ? String(Number(refs.products.find((p) => p.id === Number(l.productId))?.price) || 0) : ""}
                        onChange={(e) => setLine(l.key, { unitPrice: e.target.value })} />
                    </td>
                    <td className="num">{mnt((Number(l.quantity) || 0) * price(l))}</td>
                    <td className="act">
                      <button type="button" className="btn small" disabled={lines.length === 1} onClick={() => setLines(lines.filter((x) => x.key !== l.key))} aria-label="Мөр устгах">✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button type="button" className="btn small" style={{ marginTop: 10 }} onClick={() => setLines([...lines, blankLine()])}>+ Мөр нэмэх</button>
          <div className="total-row"><span className="muted">Нийт дүн</span><b>{mnt(total)}</b></div>
        </section>

        {error && <p className="alert" role="alert">{error}</p>}
        <div className="actions">
          <a className="btn" href={editing ? `#order/${id}` : "#orders"} style={{ textDecoration: "none" }}>Болих</a>
          <button className="btn primary" disabled={!valid || busy}>{busy ? "Хадгалж байна…" : "Хадгалах"}</button>
        </div>
      </form>
    </>
  );
}
