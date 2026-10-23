# Finance frontend

React + Vite UI for the finance module (Хураангуй, Нэхэмжлэх, Төлбөр, Зардал).

```bash
cd modules/finance/frontend
npm install
npm run dev      # http://localhost:5173, proxies /api -> http://localhost:8000
npm run build    # output in dist/
```

## Backend connection

`src/api.js` calls `GET/POST /api/finance/{invoices,payments,expenses}` (implemented in
`modules/finance/backend`, requires `finance:read` / `finance:write`). If a request fails
(e.g. not logged in, backend down) the UI falls back to demo data stored in the browser
(localStorage) and shows a notice in the sidebar.

Shapes:

- invoice: `{ id, number, customer, issued, due, amount, paid }` (dates `YYYY-MM-DD`)
- payment: `{ id, invoiceId, date, amount, method: "transfer"|"cash"|"card" }`
- expense: `{ id, date, category, vendor, amount, status: "paid"|"pending" }`

The backend endpoints need a `Authorization: Bearer <token>` header; `src/api.js` does not
send one yet, so until login is added to the UI it stays in demo mode.
