# ERP frontend (shell)

React + Vite. Neg app: login, role-d tohirsn menu, modul bur `#/<modul>/<huudas>` route-oor.

```bash
# 1) backend (repo root):  uvicorn main:app --reload      -> :8000
# 2) frontend:
cd frontend
npm install
npm run dev      # http://localhost:5173  (/api -> http://localhost:8000)
npm run build
```
Dev nevtreh: `admin / admin12345` (root README.md-g harna).

## Yaaj ajillah ve
- `src/lib/api.js` - fetch wrapper. Token `localStorage["erp.token"]`, `Authorization: Bearer`. Backend-iin `{error:{message}}`-g Error bolgono. 401 irvel `erp:unauthorized` event -> avtomataar logout.
- `src/lib/auth.jsx` - `useAuth()`: `user, login, logout, can("orders:write")`. Anh achaalahad `/api/auth/me`-eer token shalgana.
- `src/lib/permissions.js` - `core/permissions.py`-iin tsogts (**backend deer role/permission uurchilvul END shinechil**). Zuvhun menu nuuh/haruulahad; jinhene erhiig backend shalgana.
- `src/modules.js` - modul burtgel. Menu `perm` (read erh)-eer shuugdene.

## Shine modul nemeh (modul-iin ezen)
1. `modules/<modul>/frontend/src/<Modul>Module.jsx` uusgene: `export default function ({ sub, go }) {...}` (`sub` = odoogiin huudas).
2. `src/modules.js` dotor modulin bichiltiig `ready: true, Component: lazy(() => import("@<modul>/<Modul>Module"))` bolgono, `pages` jagsaaltaa zaana. (`@<modul>` alias `vite.config.js`-d bii.)
3. API: finance-iin `api.js`-g jishee bolgon `fetch` + `localStorage["erp.token"]` ashiglana (modul uuriin standalone-oor ch ajillana).
4. Stil: `src/styles.css`-iin class-uud (`panel`, `btn`, `table`, `pill`, `toolbar`, `modal`...).

## Finance
`modules/finance/frontend/src/FinanceModule.jsx` shell dotor ajillana. Token-toi bol real data, backend aldaatai bol demo data + banner haragdana. Standalone (`modules/finance/frontend` dotor `npm run dev`) mon ajillana.
