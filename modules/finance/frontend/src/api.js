import { seedInvoices, seedPayments, seedExpenses } from "./data";

// The backend (modules/finance/backend/router.py) only has /health today.
// Each call tries the real endpoint first; on failure it falls back to
// browser-local demo data so the UI is fully usable. Delete the fallback
// once the backend implements /invoices, /payments and /expenses.
const BASE = "/api/finance";
const KEY = "finance-demo-v1";
let mode = "demo";
const listeners = new Set();
export const onMode = (fn) => { listeners.add(fn); fn(mode); return () => listeners.delete(fn); };
const setMode = (m) => { if (m !== mode) { mode = m; listeners.forEach((f) => f(m)); } };

const load = () => {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return { invoices: seedInvoices, payments: seedPayments, expenses: seedExpenses };
};
const save = (db) => { try { localStorage.setItem(KEY, JSON.stringify(db)); } catch { /* ignore */ } };

async function remote(path, options) {
  const res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

export async function list(resource) {
  try {
    const data = await remote("/" + resource);
    if (Array.isArray(data)) { setMode("live"); return data; }
    throw new Error("shape");
  } catch {
    setMode("demo");
    return load()[resource];
  }
}

export async function create(resource, item) {
  try {
    const saved = await remote("/" + resource, { method: "POST", body: JSON.stringify(item) });
    setMode("live");
    return saved;
  } catch {
    setMode("demo");
    const db = load();
    const id = Math.max(0, ...db[resource].map((r) => r.id)) + 1;
    const row = { ...item, id };
    if (resource === "invoices") row.number = `НХ-2026-${String(id).padStart(4, "0")}`;
    db[resource] = [...db[resource], row];
    // Recording a payment also reduces the invoice balance.
    if (resource === "payments") {
      db.invoices = db.invoices.map((i) => (i.id === item.invoiceId ? { ...i, paid: i.paid + item.amount } : i));
    }
    save(db);
    return row;
  }
}

export const resetDemo = () => { try { localStorage.removeItem(KEY); } catch { /* ignore */ } };
