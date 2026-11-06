import { useCallback, useEffect, useState } from "react";
import { list, onMode } from "./api";
import Dashboard from "./pages/Dashboard";
import Invoices from "./pages/Invoices";
import Payments from "./pages/Payments";
import Expenses from "./pages/Expenses";

const PAGES = [
  { id: "dashboard", label: "Хураангуй", C: Dashboard },
  { id: "invoices", label: "Нэхэмжлэх", C: Invoices },
  { id: "payments", label: "Төлбөр", C: Payments },
  { id: "expenses", label: "Зардал", C: Expenses },
];

const fromHash = () => (PAGES.find((p) => "#" + p.id === location.hash) || PAGES[0]).id;

export default function App() {
  const [page, setPage] = useState(fromHash);
  const [data, setData] = useState(null);
  const [mode, setMode] = useState("demo");

  const refresh = useCallback(async () => {
    const [invoices, payments, expenses] = await Promise.all([list("invoices"), list("payments"), list("expenses")]);
    setData({ invoices, payments, expenses });
  }, []);

  useEffect(() => { refresh(); return onMode(setMode); }, [refresh]);
  useEffect(() => {
    const h = () => setPage(fromHash());
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);

  const Current = PAGES.find((p) => p.id === page).C;

  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <strong>Logistics ERP</strong>
            <span>Санхүү</span>
          </div>
        </div>
        <nav aria-label="Санхүүгийн цэс">
          {PAGES.map((p) => (
            <a key={p.id} href={"#" + p.id} className={p.id === page ? "active" : ""} aria-current={p.id === page ? "page" : undefined}>
              {p.label}
            </a>
          ))}
        </nav>
        {mode === "demo" && (
          <p className="demo-note">
            Backend холбогдоогүй тул туршилтын өгөгдөл харуулж байна. Өөрчлөлт зөвхөн энэ хөтөч дээр хадгалагдана.
          </p>
        )}
      </aside>
      <main className="main">
        {data ? <Current data={data} refresh={refresh} /> : <p className="muted">Ачаалж байна…</p>}
      </main>
    </div>
  );
}
