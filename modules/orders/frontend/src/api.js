// Thin fetch wrapper for the FastAPI backend. Token lives in localStorage ("erp-token").
const BASE = "/api";
const KEY = "erp-token";

let token = null;
try { token = localStorage.getItem(KEY); } catch { /* storage blocked */ }

// Өөр таб дээр нэвтрэх/гарах үед энэ табыг шинэчилнэ (хуучин хэрэглэгчийн эрх үлдэхгүй).
window.addEventListener("storage", (e) => {
  if (e.key === KEY && e.newValue !== token) location.reload();
});

const listeners = new Set();
export const onLoggedOut = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };
export const hasToken = () => Boolean(token);

export function setToken(t) {
  token = t;
  try { t ? localStorage.setItem(KEY, t) : localStorage.removeItem(KEY); } catch { /* ignore */ }
}

export class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

function messageOf(data, status) {
  if (data?.error?.message) return data.error.message;
  if (Array.isArray(data?.detail)) {
    return data.detail.map((d) => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`).join("; ");
  }
  if (typeof data?.detail === "string") return data.detail;
  return `Алдаа ${status}`;
}

async function request(path, { method = "GET", body, query } = {}) {
  const qs = query
    ? "?" + new URLSearchParams(Object.entries(query).filter(([, v]) => v !== "" && v != null)).toString()
    : "";
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(BASE + path + qs, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError(0, "Серверт холбогдож чадсангүй");
  }
  if (res.status === 204) return null;
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) {
    if (res.status === 401 && token) { setToken(null); listeners.forEach((f) => f()); }
    throw new ApiError(res.status, messageOf(data, res.status));
  }
  return data;
}

// auth
export const logout = () => { setToken(null); listeners.forEach((f) => f()); };
export const me = () => request("/auth/me");

// masterdata (read-only lookups for the selects)
export const lookup = async (kind) => (await request(`/masterdata/${kind}`, { query: { size: 200 } })).items;

// orders
export const listOrders = (query) => request("/orders", { query });
export const getOrder = (id) => request(`/orders/${id}`);
export const createOrder = (body) => request("/orders", { method: "POST", body });
export const updateOrder = (id, body) => request(`/orders/${id}`, { method: "PATCH", body });
export const deleteOrder = (id) => request(`/orders/${id}`, { method: "DELETE" });
export const changeStatus = (id, to, note) => request(`/orders/${id}/status`, { method: "POST", body: { to, note: note || null } });
