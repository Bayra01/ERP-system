"""Sanhuugiin tailang Excel (.xlsx) bolgon gargana: GET /api/finance/reports/export.

Sheet-uud: Toim, Saryn urgal (+ grafik), Avlagyn nasjilt, Zardal angillaar, Avlagatai harilcagch,
Nehemjleh, Tulbur, Zardal. Dungiin niilber Excel-iin SUM tomyogoor (hereglegch zasahad dahin tootsno).
"""
from datetime import date, datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.masterdata.backend.models import Customer
from modules.orders.backend.models import Order

from . import service
from .models import Expense, Invoice, Payment

MONEY = '#,##0 "₮"'
PCT = "0.0%"
ACCENT = "0E7C86"
HEAD_FILL = PatternFill("solid", fgColor="DFF1F2")
TOTAL_FILL = PatternFill("solid", fgColor="F2F5F7")
LINE = Side(style="thin", color="DCE3E9")
AGE = {"current": "Хугацаа болоогүй", "1-30": "1–30 хоног хэтэрсэн", "31-60": "31–60 хоног",
       "61-90": "61–90 хоног", "90+": "90+ хоног"}
STATUS = {"paid": "Төлөгдсөн", "partial": "Хэсэгчлэн", "unpaid": "Төлөгдөөгүй", "overdue": "Хугацаа хэтэрсэн"}
METHOD = {"bank": "Банк", "cash": "Бэлэн", "card": "Карт"}
EXP_STATUS = {"paid": "Төлсөн", "pending": "Төлөгдөөгүй"}


def _month(m: str) -> str:
    y, mo = m.split("-")
    return f"{y} оны {int(mo)}-р сар"


def _table(ws, row: int, headers: list[str], rows: list[list], money_cols=(), pct_cols=(),
           total: str | None = None, widths: list[int] | None = None) -> int:
    """headers + rows-g row-oos ehluulj bichne; total bol money_cols-d SUM mor nemne. Daraagiin mor butsaana."""
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font, cell.fill = Font(bold=True), HEAD_FILL
        cell.border = Border(bottom=LINE)
        cell.alignment = Alignment(horizontal="right" if c in money_cols or c in pct_cols else "left",
                                   vertical="center")
    first = row + 1
    for r, values in enumerate(rows, start=first):
        for c, v in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = Border(bottom=LINE)
            if c in money_cols:
                cell.number_format = MONEY
            elif c in pct_cols:
                cell.number_format = PCT
    last = first + len(rows) - 1
    nxt = last + 1
    if total is not None:
        ws.cell(row=nxt, column=1, value=total).font = Font(bold=True)
        for c in range(1, len(headers) + 1):
            ws.cell(row=nxt, column=c).fill = TOTAL_FILL
        for c in money_cols:
            col = get_column_letter(c)
            cell = ws.cell(row=nxt, column=c, value=f"=SUM({col}{first}:{col}{last})" if rows else 0)
            cell.number_format, cell.font = MONEY, Font(bold=True)
        nxt += 1
    for c, w in enumerate(widths or [], start=1):
        ws.column_dimensions[get_column_letter(c)].width = w
    return nxt


def _sheet(wb, title: str, heading: str, period: str):
    ws = wb.create_sheet(title)
    ws["A1"] = heading
    ws["A1"].font = Font(bold=True, size=13, color=ACCENT)
    ws["A2"] = period
    ws["A2"].font = Font(color="5A6975")
    ws.freeze_panes = "A5"
    return ws


def build_report(db: Session, start: date, end: date, user_name: str) -> bytes:
    rep = service.report(db, start, end)
    t = rep["totals"]
    period = f"Хугацаа: {start:%Y-%m-%d} – {end:%Y-%m-%d}"
    wb = Workbook()

    # ---- Toim
    ws = wb.active
    ws.title = "Тойм"
    ws["A1"] = "Санхүүгийн тайлан"
    ws["A1"].font = Font(bold=True, size=16, color=ACCENT)
    ws["A2"] = period
    ws["A3"] = f"Гаргасан: {datetime.now():%Y-%m-%d %H:%M} · {user_name}"
    for c in ("A2", "A3"):
        ws[c].font = Font(color="5A6975")
    kpi = [["Нэхэмжилсэн (хугацаанд)", t["invoiced"]], ["Орсон төлбөр (хугацаанд)", t["collected"]],
           ["Зардал (хугацаанд)", t["expenses"]], ["Цэвэр мөнгөн урсгал", t["net"]],
           ["Нийт авлага (өнөөдрийн байдлаар)", t["outstanding"]],
           ["Хугацаа хэтэрсэн авлага", t["overdue"]]]
    _table(ws, 5, ["Үзүүлэлт", "Дүн"], kpi, money_cols=(2,), widths=[38, 20])
    ws["A13"] = "Цэвэр мөнгөн урсгал = Орсон төлбөр − Зардал. Авлага, насжилт өнөөдрийн байдлаар."
    ws["A13"].font = Font(italic=True, color="5A6975", size=9)

    # ---- Saryn urgal + grafik
    ws = _sheet(wb, "Сарын урсгал", "Сарын мөнгөн урсгал", period)
    rows = [[_month(m["month"]), m["invoiced"], m["collected"], m["expenses"], None] for m in rep["monthly"]]
    for i, r in enumerate(rows, start=5):
        r[4] = f"=C{i}-D{i}"
    end_row = _table(ws, 4, ["Сар", "Нэхэмжилсэн", "Орсон төлбөр", "Зардал", "Цэвэр урсгал"], rows,
                     money_cols=(2, 3, 4, 5), total="Нийт", widths=[20, 18, 18, 18, 18])
    if rows:
        chart = BarChart()
        chart.type, chart.grouping, chart.title = "col", "clustered", "Сарын мөнгөн урсгал"
        chart.y_axis.title, chart.y_axis.numFmt = "₮", "#,##0"
        chart.add_data(Reference(ws, min_col=2, max_col=4, min_row=4, max_row=4 + len(rows)), titles_from_data=True)
        chart.set_categories(Reference(ws, min_col=1, min_row=5, max_row=4 + len(rows)))
        for s, color in zip(chart.series, ("2A78D6", "EB6834", "1BAF7A")):  # UI-iin grafiktai ijil ungu
            s.graphicalProperties.solidFill = color
            s.graphicalProperties.line.solidFill = color
        chart.height, chart.width = 8, 22
        ws.add_chart(chart, f"A{end_row + 2}")

    # ---- Avlagyn nasjilt
    ws = _sheet(wb, "Авлагын насжилт", "Авлагын насжилт (өнөөдрийн байдлаар)", f"Огноо: {date.today():%Y-%m-%d}")
    _table(ws, 4, ["Ангилал", "Нэхэмжлэх", "Дүн"],
           [[AGE[a["bucket"]], a["count"], a["amount"]] for a in rep["aging"]],
           money_cols=(3,), total="Нийт", widths=[26, 14, 20])

    # ---- Zardal angillaar
    ws = _sheet(wb, "Зардал ангиллаар", "Зардал ангиллаар", period)
    cats = rep["expenses_by_category"]
    n = len(cats)
    _table(ws, 4, ["Ангилал", "Дүн", "Хувь"],
           [[c["category"], c["amount"], f"=B{5 + i}/SUM($B$5:$B${4 + n})"] for i, c in enumerate(cats)],
           money_cols=(2,), pct_cols=(3,), total="Нийт", widths=[28, 20, 12])

    # ---- Avlagatai harilcagch
    ws = _sheet(wb, "Авлагатай харилцагч", "Их авлагатай харилцагчид", f"Огноо: {date.today():%Y-%m-%d}")
    _table(ws, 4, ["Харилцагч", "Нэхэмжлэх", "Хэтэрсэн", "Үлдэгдэл"],
           [[d["customer"], d["invoices"], d["overdue"], d["balance"]] for d in rep["top_debtors"]],
           money_cols=(3, 4), total="Нийт", widths=[32, 12, 18, 18])

    # ---- Nehemjleh (hugatsaand gargasan)
    invs = db.execute(select(Invoice, Customer.name, Order.order_no)
                      .join(Customer, Customer.id == Invoice.customer_id)
                      .outerjoin(Order, Order.id == Invoice.order_id)
                      .where(Invoice.issued.between(start, end)).order_by(Invoice.issued, Invoice.id)).all()
    ws = _sheet(wb, "Нэхэмжлэх", "Хугацаанд гаргасан нэхэмжлэх", period)
    end_row = _table(ws, 4, ["Дугаар", "Харилцагч", "Захиалга", "Огноо", "Төлөх", "Дүн", "Төлсөн", "Үлдэгдэл", "Төлөв"],
                     [[i.number, cn, ono or "", i.issued, i.due, float(i.amount), float(i.paid),
                       float(i.amount - i.paid), STATUS[service.invoice_status(i)]] for i, cn, ono in invs],
                     money_cols=(6, 7, 8), total="Нийт", widths=[20, 28, 20, 12, 12, 16, 16, 16, 18])
    _dates(ws, (4, 5), 5, end_row)
    if invs:
        ws.auto_filter.ref = f"A4:I{4 + len(invs)}"

    # ---- Tulbur
    pays = db.execute(select(Payment, Invoice.number, Customer.name)
                      .join(Invoice, Invoice.id == Payment.invoice_id)
                      .join(Customer, Customer.id == Invoice.customer_id)
                      .where(Payment.date.between(start, end)).order_by(Payment.date, Payment.id)).all()
    ws = _sheet(wb, "Төлбөр", "Хугацаанд орсон төлбөр", period)
    end_row = _table(ws, 4, ["Огноо", "Нэхэмжлэх", "Харилцагч", "Хэлбэр", "Дүн"],
                     [[p.date, num, cn, METHOD.get(p.method, p.method), float(p.amount)] for p, num, cn in pays],
                     money_cols=(5,), total="Нийт", widths=[12, 20, 28, 12, 18])
    _dates(ws, (1,), 5, end_row)

    # ---- Zardal
    exps = db.scalars(select(Expense).where(Expense.date.between(start, end))
                      .order_by(Expense.date, Expense.id)).all()
    ws = _sheet(wb, "Зардал", "Хугацааны зардал", period)
    end_row = _table(ws, 4, ["Огноо", "Ангилал", "Нийлүүлэгч", "Төлөв", "Дүн"],
                     [[e.date, e.category, e.vendor, EXP_STATUS.get(e.status, e.status), float(e.amount)]
                      for e in exps], money_cols=(5,), total="Нийт", widths=[12, 22, 28, 14, 18])
    _dates(ws, (1,), 5, end_row)
    if exps:
        ws.auto_filter.ref = f"A4:E{4 + len(exps)}"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _dates(ws, cols, first: int, end_row: int) -> None:
    for c in cols:
        for r in range(first, end_row):
            ws.cell(row=r, column=c).number_format = "yyyy-mm-dd"
