"""Finance: nehemjleh (Invoice), tulbur (Payment), zardal (Expense).

Sonsdog event:
  order.delivered -> zahialgiin nehemjleh uusgene (1 zahialga = 1 nehemjleh, dahin ireh ni davhardahgui)
"""
import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from core import events
from core.audit import log_action
from core.database import SessionLocal
from core.exceptions import ConflictError, NotFoundError, UnprocessableError
from modules.masterdata.backend.models import Customer

from .models import Expense, Invoice, Payment
from .schemas import ExpenseCreate, InvoiceCreate, PaymentCreate

log = logging.getLogger("erp.finance")
PAYMENT_TERM_DAYS = 30


# ---------- Invoice ----------
def _number(inv: Invoice) -> str:
    return f"НХ-{inv.issued.year}-{inv.id:04d}"


def _customer(db: Session, data: InvoiceCreate) -> Customer:
    if data.customer_id is not None:
        c = db.get(Customer, data.customer_id)
        if c is None or getattr(c, "deleted_at", None) is not None:
            raise UnprocessableError("Kharitsagch oldsongui")
        return c
    if not data.customer:
        raise UnprocessableError("customer esvel customer_id zaaval")
    name = data.customer.strip()
    c = db.scalars(select(Customer).where(Customer.name == name)).first()
    if c is None:  # UI-d shine ner bichij bolno -> kharitsagch uusgene
        c = Customer(code="TMP", name=name)
        db.add(c)
        db.flush()
        c.code = f"AUTO-{c.id}"
    return c


def create_invoice(db: Session, data: InvoiceCreate, user_id: int | None) -> Invoice:
    if data.due < data.issued:
        raise UnprocessableError("Tulukh ognoo nehemjlehiin ognoonoos umnu baij bolohgui")
    c = _customer(db, data)
    inv = Invoice(customer_id=c.id, issued=data.issued, due=data.due, amount=data.amount,
                  paid=Decimal(0), notes=data.notes, created_by=user_id)
    db.add(inv)
    db.flush()
    inv.number = _number(inv)
    db.commit()
    log_action(db, user_id, "create", "finance.Invoice", inv.id, {"amount": str(inv.amount)})
    return inv


def get_invoice(db: Session, invoice_id: int) -> Invoice:
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise NotFoundError("Nehemjleh oldsongui")
    return inv


def list_invoices(db: Session, customer_id: int | None = None, order_id: int | None = None,
                  limit: int = 1000, offset: int = 0) -> list[Invoice]:
    stmt = select(Invoice).order_by(Invoice.id)
    if customer_id is not None:
        stmt = stmt.where(Invoice.customer_id == customer_id)
    if order_id is not None:
        stmt = stmt.where(Invoice.order_id == order_id)
    return list(db.scalars(stmt.limit(limit).offset(offset)).all())


def customer_names(db: Session, invoices: list[Invoice]) -> dict[int, str]:
    ids = {i.customer_id for i in invoices}
    if not ids:
        return {}
    rows = db.execute(select(Customer.id, Customer.name).where(Customer.id.in_(ids))).all()
    return {cid: name for cid, name in rows}


def invoice_dict(inv: Invoice, names: dict[int, str]) -> dict:
    return {"id": inv.id, "number": inv.number, "customer": names.get(inv.customer_id, ""),
            "customerId": inv.customer_id, "orderId": inv.order_id, "issued": inv.issued,
            "due": inv.due, "amount": inv.amount, "paid": inv.paid}


# ---------- Payment ----------
def create_payment(db: Session, data: PaymentCreate, user_id: int | None) -> Payment:
    inv = db.scalars(select(Invoice).where(Invoice.id == data.invoiceId).with_for_update()).first()
    if inv is None:
        raise NotFoundError("Nehemjleh oldsongui")
    balance = inv.amount - inv.paid
    if balance <= 0:
        raise ConflictError("Ene nehemjleh buten tulugdsun baina")
    if data.amount > balance:
        raise UnprocessableError(f"Tulburiin dun uldegdelees ({balance}) ih baij bolohgui")
    pay = Payment(invoice_id=inv.id, date=data.date, amount=data.amount,
                  method=data.method.value, created_by=user_id)
    inv.paid = inv.paid + data.amount
    db.add(pay)
    db.commit()
    log_action(db, user_id, "create", "finance.Payment", pay.id,
               {"invoice_id": inv.id, "amount": str(pay.amount)})
    return pay


def list_payments(db: Session, invoice_id: int | None = None,
                  limit: int = 1000, offset: int = 0) -> list[Payment]:
    stmt = select(Payment).order_by(Payment.id)
    if invoice_id is not None:
        stmt = stmt.where(Payment.invoice_id == invoice_id)
    return list(db.scalars(stmt.limit(limit).offset(offset)).all())


# ---------- Expense ----------
def create_expense(db: Session, data: ExpenseCreate, user_id: int | None) -> Expense:
    exp = Expense(date=data.date, category=data.category.strip(), vendor=data.vendor.strip(),
                  amount=data.amount, status=data.status.value, created_by=user_id)
    db.add(exp)
    db.commit()
    log_action(db, user_id, "create", "finance.Expense", exp.id, {"amount": str(exp.amount)})
    return exp


def list_expenses(db: Session, category: str | None = None, status: str | None = None,
                  limit: int = 1000, offset: int = 0) -> list[Expense]:
    stmt = select(Expense).order_by(Expense.id)
    if category:
        stmt = stmt.where(Expense.category == category)
    if status:
        stmt = stmt.where(Expense.status == status)
    return list(db.scalars(stmt.limit(limit).offset(offset)).all())


# ---------- Events ----------
def invoice_for_order(db: Session, p: dict) -> Invoice | None:
    order_id = p["order_id"]
    if db.scalars(select(Invoice).where(Invoice.order_id == order_id)).first():
        return None  # davhardahgui
    amount = Decimal(str(p.get("total_amount") or 0))
    if amount <= 0:
        return None
    today = date.today()
    inv = Invoice(customer_id=p["customer_id"], order_id=order_id, issued=today,
                  due=today + timedelta(days=PAYMENT_TERM_DAYS), amount=amount, paid=Decimal(0),
                  notes=f"Zahialga {p.get('order_no') or order_id}")
    db.add(inv)
    db.flush()
    inv.number = _number(inv)
    db.commit()
    log_action(db, None, "create", "finance.Invoice", inv.id, {"order_id": order_id, "auto": True})
    return inv


@events.subscribe("order.delivered")
def on_order_delivered(p: dict) -> None:
    with SessionLocal() as db:
        invoice_for_order(db, p)
