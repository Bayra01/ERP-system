# erp_frontend — Агуулах ба Тээвэр

Энгийн HTML/CSS/JS (build хэрэггүй). FastAPI backend өөрөө serve хийнэ:

```bash
uvicorn main:app --reload
# http://localhost:8000/erp-ui
```

- `views/index.html` → `GET /erp-ui`
- `static/` → `/erp_frontend/static/...`
- `static/src/js/app.js` нь `/api/...` руу JWT-тэй хандана. Token `localStorage["erp-token"]`-д
  хадгалагдах бөгөөд захиалгын React апп (`/orders/`)-тай нэг origin дээр хуваалцна — нэг удаа нэвтэрнэ.

Табууд (эрхээр харагдана):

| Таб | Файл | Эрх |
|---|---|---|
| Агуулахын менежмент | `js/app.js` | `warehouse:read` |
| Тээврийн удирдлага | `js/app.js` | `transport:read` |
| Маршрут — газрын зураг, оновчлол, ↑↓ гараар дараалал, координат оруулах | `js/route.js` | `routing:read` (засах: `routing:write`) |
| Санхүү — KPI, сарын урсгал, авлагын насжилт, зардал, нэхэмжлэх/төлбөр | `js/finance.js` | `finance:read` (бүртгэх: `finance:write`) |
| Мэдэгдэл — системийн мэдэгдэл, хэрэглэгч/бүлэг рүү мессеж, хариулах, илгээсэн | `js/notify.js` | бүх хэрэглэгч |

Дизайн нь захиалгын React апптай (`modules/orders/frontend/src/styles.css`) ижил токен, бүтэцтэй: хажуугийн цэс,
`page-head` + `panel` + `pill` + `chip`, формууд modal (`openModal(id)` / `closeModal()`). Хоёр апп бие биеийн модуль руу
хажуугийн цэсээр холбогдоно (`/orders/` ↔ `/erp-ui#wh|tr|rt|fn|nt`).

Нэвтрэлт: `views/login.html` + `js/login.js` → `/login` (модуль сонгох), `/login/<модуль>`. Эрхгүй модульд backend
403 буцааж, нэвтэрч болох модулиудыг санал болгоно. Нэвтрээгүй үед `/erp-ui` болон `/orders/` өөрсдөө
`/login/<модуль>?next=...` руу шилжүүлнэ. «Ажилтнууд» таб (`js/users.js`) зөвхөн админд.

Шинэ таб нэмэх: `TABS.<id>={perm,render}` гэж бүртгээд `index.html`-д `t-<id>` товч, `<section id="<id>">` нэмнэ.

Ашигладаг endpoint: `/api/auth/*`, `/api/masterdata/{locations,products}`, `/api/warehouse/*`,
`/api/transport/*`, `/api/routing/*`, `/api/finance/*` (`/reports/summary`), `/api/notifications/*`, `/api/orders` (дугаар харуулахад).

Товчнууд `GET /api/auth/me`-ийн `permissions`-оор харагдана/нуугдана; бодит хяналт backend дээр.

`__manifest__.py`, `controllers/` нь хуучин Odoo addon хувилбарын үлдэгдэл — FastAPI-д ашиглагдахгүй.
