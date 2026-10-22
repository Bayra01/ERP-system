# Finance frontend

React + Vite UI for the finance module (Хураангуй, Нэхэмжлэх, Төлбөр, Зардал).

```bash
cd modules/finance/frontend
npm install
npm run dev      # http://localhost:5173, proxies /api -> http://localhost:8000
npm run build    # output in dist/
```

## Backend connection

`src/api.js` calls `GET/POST /api/finance/{invoices,payments,expenses}`.
The backend currently only exposes `/health`, so on failure the UI falls back
to demo data stored in the browser (localStorage) and shows a notice in the sidebar.
Once the endpoints exist, the notice disappears automatically.

Expected shapes:

- invoice: `{ id, number, customer, issued, due, amount, paid }` (dates `YYYY-MM-DD`)
- payment: `{ id, invoiceId, date, amount, method: "transfer"|"cash"|"card" }`
- expense: `{ id, date, category, vendor, amount, status: "paid"|"pending" }`

Note: `modules/finance/backend/router.py` sets `prefix="/api/finance"` and `main.py`
adds the same prefix again, so the health route is currently `/api/finance/api/finance/health`.
Remove one of the two prefixes when implementing the endpoints.
