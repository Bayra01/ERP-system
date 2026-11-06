from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import ConflictError, NotFoundError, UnprocessableError
from modules.masterdata.backend.models import Customer

from .models import Expense, Invoice, Payment

DUE_DAYS = 30
CENT = Decimal("0.01")


def money(v) -> Decimal:
    return Decimal(str(v)).quantize(CENT)


def get_invoice(db: Session, invoice_id: int) -> Invoice:
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise NotFoundError(f"Nehemjleh #{invoice_id} oldsongui")
    return inv


def resolve_customer(db: Session, customer_id: int | None, name: str | None) -> Customer:
    if customer_id is not None:
        c = db.get(Customer, customer_id)
        if c is None or c.deleted_at is not None:
            raise UnprocessableError(f"Harilcagch #{customer_id} oldsongui")
        return c
    if not name or not name.strip():
        raise UnprocessableError("customer esvel customerId shaardlagatai")
    name = name.strip()
    c = db.scalar(select(Customer).where(Customer.name == name, Customer.deleted_at.is_(None)))
    if c is None:
        c = Customer(name=name, code="", type="company")
        db.add(c)
        db.flush()
        c.code = f"AUTO-{c.id}"
    return c


def create_invoice(db: Session, customer_id: int, amount, user_id: int | None,
                   order_id: int | None = None, issued: date | None = None,
                   due: date | None = None, notes: str | None = None) -> Invoice:
    if order_id is not None and db.scalar(select(Invoice.id).where(Invoice.order_id == order_id)):
        raise ConflictError(f"Zahialga #{order_id}-d nehemjleh uusgegdsen")
    issued = issued or date.today()
    inv = Invoice(customer_id=customer_id, order_id=order_id, issued=issued,
                  due=due or issued + timedelta(days=DUE_DAYS), amount=money(amount),
                  paid=Decimal(0), notes=notes, created_by=user_id)
    db.add(inv)
    db.flush()
    inv.number = f"INV-{issued:%Y%m}-{inv.id:06d}"
    db.commit()
    return inv


def add_payment(db: Session, invoice_id: int, amount, method: str, on: date | None,
                user_id: int | None) -> Payment:
    inv = get_invoice(db, invoice_id)
    balance = Decimal(inv.amount) - Decimal(inv.paid)
    if balance <= 0:
        raise ConflictError(f"{inv.number} buren tulugdsun")
    amt = money(amount)
    if amt > balance:
        raise UnprocessableError(f"Tulbur uldegdlees ({balance}) ih baina")
    p = Payment(invoice_id=inv.id, date=on or date.today(), amount=amt, method=method,
                created_by=user_id)
    db.add(p)
    inv.paid = Decimal(inv.paid) + amt
    db.commit()
    return p


def invoice_status(inv: Invoice) -> str:
    amount, paid = Decimal(inv.amount), Decimal(inv.paid)
    if paid >= amount:
        return "paid"
    if inv.due < date.today():
        return "overdue"
    return "partial" if paid > 0 else "unpaid"


# ---------------- Tailan
# (bucket, hotsorson honog: dood, deed). current = tulukh hugatsaa boloogui.
AGING = [("current", None, 0), ("1-30", 1, 30), ("31-60", 31, 60), ("61-90", 61, 90),
         ("90+", 91, None)]


def _months(start: date, end: date) -> list[str]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def report(db: Session, start: date, end: date) -> dict:
    """Hugatsaanii urgal (start..end) + ugiin bairdal (avlaga, nasjilt - unuudriin baidlaar)."""
    today = date.today()
    months = {k: {"month": k, "invoiced": 0.0, "collected": 0.0, "expenses": 0.0}
              for k in _months(start, end)}
    invoices = db.execute(select(Invoice, Customer.name)
                          .join(Customer, Customer.id == Invoice.customer_id)).all()
    payments = db.scalars(select(Payment).where(Payment.date.between(start, end))).all()
    expenses = db.scalars(select(Expense).where(Expense.date.between(start, end))).all()

    invoiced = 0.0
    for inv, _ in invoices:
        if start <= inv.issued <= end:
            invoiced += float(inv.amount)
            months[f"{inv.issued:%Y-%m}"]["invoiced"] += float(inv.amount)
    for p in payments:
        months[f"{p.date:%Y-%m}"]["collected"] += float(p.amount)
    by_cat: dict[str, float] = {}
    for e in expenses:
        months[f"{e.date:%Y-%m}"]["expenses"] += float(e.amount)
        by_cat[e.category] = by_cat.get(e.category, 0.0) + float(e.amount)

    aging = {k: {"bucket": k, "amount": 0.0, "count": 0} for k, _, _ in AGING}
    debtors: dict[str, dict] = {}
    for inv, cname in invoices:
        bal = float(inv.amount) - float(inv.paid)
        if bal <= 0:
            continue
        late = (today - inv.due).days
        key = next(k for k, lo, hi in AGING
                   if (lo is None and late <= 0) or (lo is not None and late >= lo
                                                     and (hi is None or late <= hi)))
        aging[key]["amount"] += bal
        aging[key]["count"] += 1
        d = debtors.setdefault(cname, {"customer": cname, "balance": 0.0, "invoices": 0,
                                       "overdue": 0.0})
        d["balance"] += bal
        d["invoices"] += 1
        d["overdue"] += bal if late > 0 else 0.0

    collected = sum(float(p.amount) for p in payments)
    spent = sum(by_cat.values())
    outstanding = sum(a["amount"] for a in aging.values())
    return {
        "from": start, "to": end,
        "totals": {"invoiced": invoiced, "collected": collected, "expenses": spent,
                   "net": collected - spent, "outstanding": outstanding,
                   "overdue": outstanding - aging["current"]["amount"]},
        "monthly": [{k: round(v, 2) if isinstance(v, float) else v for k, v in m.items()}
                    for m in months.values()],
        "aging": list(aging.values()),
        "expenses_by_category": sorted(({"category": k, "amount": round(v, 2)}
                                        for k, v in by_cat.items()), key=lambda r: -r["amount"]),
        "top_debtors": sorted(debtors.values(), key=lambda r: -r["balance"])[:10],
    }
