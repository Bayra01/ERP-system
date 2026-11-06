export const TODAY = new Date("2026-10-16T00:00:00");

export const mnt = (n) =>
  new Intl.NumberFormat("mn-MN", { maximumFractionDigits: 0 }).format(Math.round(n)) + " ₮";

export const mntShort = (n) => {
  const a = Math.abs(n);
  if (a >= 1e9) return (n / 1e9).toFixed(1) + " тэрбум";
  if (a >= 1e6) return (n / 1e6).toFixed(1) + " сая";
  if (a >= 1e3) return Math.round(n / 1e3) + " мянга";
  return String(Math.round(n));
};

export const dayDiff = (iso) => Math.round((new Date(iso + "T00:00:00") - TODAY) / 86400000);

export const invoiceStatus = (inv) => {
  if (inv.paid >= inv.amount) return "paid";
  if (dayDiff(inv.due) < 0) return "overdue";
  if (inv.paid > 0) return "partial";
  return "open";
};

export const STATUS_LABEL = {
  paid: "Төлөгдсөн",
  overdue: "Хугацаа хэтэрсэн",
  partial: "Хэсэгчлэн төлсөн",
  open: "Хүлээгдэж буй",
};

export const METHOD_LABEL = { transfer: "Шилжүүлэг", cash: "Бэлэн мөнгө", card: "Карт" };
export const EXPENSE_CATEGORIES = ["Түлш", "Засвар үйлчилгээ", "Цалин", "Түрээс", "Даатгал", "Гааль, татвар", "Бусад"];
