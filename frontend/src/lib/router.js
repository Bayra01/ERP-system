import { useCallback, useEffect, useState } from "react";

// Hash router: #/<modul>/<huudas>   jishee: #/finance/invoices
const parse = () => {
  const [module = "", sub = ""] = location.hash.replace(/^#\/?/, "").split("/");
  return { module, sub };
};

export function useRoute() {
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const h = () => setRoute(parse());
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);
  const go = useCallback((module, sub = "", { replace = false } = {}) => {
    const hash = "#/" + [module, sub].filter(Boolean).join("/");
    if (replace) {
      history.replaceState(null, "", hash);
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    } else {
      location.hash = hash;
    }
  }, []);
  return [route, go];
}
