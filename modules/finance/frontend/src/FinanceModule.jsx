import { useCallback, useEffect, useState } from "react";
import { list, onMode } from "./api";
import Dashboard from "./pages/Dashboard";
import Invoices from "./pages/Invoices";
import Payments from "./pages/Payments";
import Expenses from "./pages/Expenses";

// Shell (frontend/src/modules.js) ene component-iig lazy import hiine.
// sub = "dashboard" | "invoices" | "payments" | "expenses"
const PAGES = { dashboard: Dashboard, invoices: Invoices, payments: Payments, expenses: Expenses };

export default function FinanceModule({ sub }) {
  const [data, setData] = useState(null);
  const [mode, setMode] = useState("demo");

  const refresh = useCallback(async () => {
    const [invoices, payments, expenses] = await Promise.all([list("invoices"), list("payments"), list("expenses")]);
    setData({ invoices, payments, expenses });
  }, []);

  useEffect(() => { refresh(); return onMode(setMode); }, [refresh]);

  const Current = PAGES[sub] || Dashboard;
  if (!data) return <p className="muted">Ачаалж байна…</p>;
  return (
    <>
      {mode === "demo" && (
        <p className="demo-banner">Backend-ээс өгөгдөл авч чадсангүй тул туршилтын өгөгдөл харуулж байна. Өөрчлөлт зөвхөн энэ хөтөч дээр хадгалагдана.</p>
      )}
      <Current data={data} refresh={refresh} />
    </>
  );
}
