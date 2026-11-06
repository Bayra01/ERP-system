# orders frontend

React 18 + Vite. Захиалгын модулийн UI: нэвтрэх, жагсаалт (төлөв/хайлт/харилцагч шүүлт, хуудаслалт),
шинэ захиалга үүсгэх, ноорог захиалга засах/устгах, дэлгэрэнгүй (мөр, төлвийн түүх), төлөв шилжүүлэх.

## Ажиллуулах
```bash
cd modules/orders/frontend
npm install
npm run dev        # http://localhost:5174  (/api -> http://localhost:8000 руу proxy)
npm run build
```
Backend (`uvicorn main:app --reload`) ажиллаж байх ёстой. Finance frontend (5173)-тэй зэрэг ажиллуулж болно.

## Backend холболт
`src/api.js` дараах endpoint-уудыг дууддаг (JWT token `localStorage["erp-token"]`-д хадгалагдана, 401 болбол автоматаар гарна):

- Нэвтрэлт: FastAPI-ийн `/login/orders` хуудас (`?next=` буцах хаягтай); апп өөрөө `GET /api/auth/me`
- `GET /api/masterdata/{customers,products,locations}?size=200` (select-үүдэд)
- `GET/POST /api/orders`, `GET/PATCH/DELETE /api/orders/{id}`, `POST /api/orders/{id}/status`

## Эрх
`src/perm.js` нь `core/permissions.py`-ийн orders:* эрхийг толилуулдаг, зөвхөн товчийг харуулах/нуухад ашиглана.
Бодит хяналт backend дээр хийгдэнэ.

| Дүр | Хийж чадах зүйл |
|---|---|
| admin, dispatcher | үүсгэх, засах, батлах, цуцлах, бэлтгэх, илгээх, хүргэгдсэн болгох |
| warehouse | харах, бэлтгэж эхлэх, илгээсэн болгох |
| driver | харах, хүргэгдсэн болгох |
| accountant | зөвхөн харах |
