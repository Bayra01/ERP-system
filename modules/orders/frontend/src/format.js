export const mnt = (n) =>
  new Intl.NumberFormat("mn-MN", { maximumFractionDigits: 2 }).format(Number(n) || 0) + " ₮";

export const day = (iso) => (iso ? String(iso).slice(0, 10) : "—");
export const dayTime = (iso) => (iso ? String(iso).slice(0, 16).replace("T", " ") : "—");

export const STATUSES = ["draft", "confirmed", "picking", "shipped", "delivered", "cancelled"];
export const STATUS_LABEL = {
  draft: "Ноорог",
  confirmed: "Баталсан",
  picking: "Бэлтгэж буй",
  shipped: "Илгээсэн",
  delivered: "Хүргэгдсэн",
  cancelled: "Цуцлагдсан",
};
export const ACTION_LABEL = {
  confirmed: "Батлах",
  picking: "Бэлтгэж эхлэх",
  shipped: "Илгээсэн болгох",
  delivered: "Хүргэгдсэн болгох",
  cancelled: "Цуцлах",
};
export const ROLE_LABEL = {
  admin: "Админ", user: "Хэрэглэгч", dispatcher: "Диспетчер", driver: "Жолооч", warehouse: "Агуулахын ажилтан", accountant: "Нягтлан",
};
