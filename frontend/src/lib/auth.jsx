import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, getToken, setToken, UNAUTHORIZED_EVENT } from "./api";
import { hasPermission } from "./permissions";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(() => Boolean(getToken()));

  const logout = useCallback(() => { setToken(null); setUser(null); }, []);

  // Huudas anh achaalahad token baival /me-ger shalgana.
  useEffect(() => {
    if (!getToken()) return;
    api.get("/api/auth/me").then(setUser).catch(() => setToken(null)).finally(() => setBooting(false));
  }, []);

  // Ali ch API 401 butsaaval (token duussan) garna.
  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout);
  }, [logout]);

  const login = useCallback(async (username, password) => {
    const { access_token } = await api.post("/api/auth/login", { username, password });
    setToken(access_token);
    try {
      setUser(await api.get("/api/auth/me"));
    } catch (e) {
      setToken(null);
      throw e;
    }
  }, []);

  const value = useMemo(
    () => ({ user, booting, login, logout, can: (perm) => Boolean(user) && hasPermission(user.role, perm) }),
    [user, booting, login, logout]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
