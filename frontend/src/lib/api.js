// Neg butsaasan fetch wrapper: Bearer token nemne, backend-iin {error:{message}}-g Error bolgono.
export const TOKEN_KEY = "erp.token";
export const UNAUTHORIZED_EVENT = "erp:unauthorized";

export const getToken = () => { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } };
export const setToken = (t) => { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ } };

export class ApiError extends Error {
  constructor(status, message, code) { super(message); this.status = status; this.code = code; }
}

export async function request(path, { method = "GET", body, headers } = {}) {
  const token = getToken();
  let res;
  try {
    res = await fetch(path, {
      method,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Серверт холбогдож чадсангүй. Backend ажиллаж байгаа эсэхийг шалгана уу.");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = data?.error?.message
      || (Array.isArray(data?.detail) ? "Оруулсан мэдээлэл буруу байна." : data?.detail)
      || `Алдаа (${res.status})`;
    // Login-d 401 = buruu nuuts ug; busad үед token duussan -> shell logout hiine.
    if (res.status === 401 && token) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    throw new ApiError(res.status, message, data?.error?.code);
  }
  return data;
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: "POST", body }),
  patch: (p, body) => request(p, { method: "PATCH", body }),
};
