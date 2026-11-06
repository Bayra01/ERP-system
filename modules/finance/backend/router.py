<<<<<<< HEAD
"""/api/finance - list endpoint-uud Array butsaana (Page bish)."""
from datetime import date, timedelta

from urllib.parse import quote, urlencode

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import Response
from sqlalchemy import select
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from core.audit import log_action
from core.database import get_db
from core.deps import bearer, get_current_user, require_permission
from core.exceptions import ForbiddenError, UnauthorizedError, UnprocessableError
from core.permissions import has_permission
from core.security import create_access_token, decode_access_token
from modules.auth.backend.models import User
from modules.masterdata.backend.models import Customer

from . import handlers  # noqa: F401  event handler burtgene
from . import export, service
from .models import Expense, Invoice, Payment
from .schemas import (ExpenseIn, ExpenseOut, InvoiceDetail, InvoiceIn, InvoiceOut, PaymentIn,
                      PaymentOut)

router = APIRouter(prefix="/api/finance", tags=["Finance"])
can_read = Depends(require_permission("finance:read"))
can_write = Depends(require_permission("finance:write"))


def _invoice(inv: Invoice, customer: Customer | None) -> dict:
    return {"id": inv.id, "number": inv.number, "customer": customer.name if customer else "",
            "customer_id": inv.customer_id, "order_id": inv.order_id, "issued": inv.issued,
            "due": inv.due, "amount": inv.amount, "paid": inv.paid,
            "balance": inv.amount - inv.paid, "status": service.invoice_status(inv),
            "notes": inv.notes}


def _payment(p: Payment, number: str | None) -> dict:
    return {"id": p.id, "invoice_id": p.invoice_id, "invoice_number": number, "date": p.date,
            "amount": p.amount, "method": p.method}


@router.get("/invoices", response_model=list[InvoiceOut], dependencies=[can_read])
def list_invoices(status: str | None = None, customer_id: int | None = None,
                  db: Session = Depends(get_db)):
    stmt = select(Invoice, Customer).join(Customer, Customer.id == Invoice.customer_id)
    if customer_id:
        stmt = stmt.where(Invoice.customer_id == customer_id)
    rows = [_invoice(i, c) for i, c in db.execute(stmt.order_by(Invoice.id.desc()))]
    return [r for r in rows if not status or r["status"] == status]


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetail, dependencies=[can_read])
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = service.get_invoice(db, invoice_id)
    pays = db.scalars(select(Payment).where(Payment.invoice_id == inv.id).order_by(Payment.id))
    return {**_invoice(inv, db.get(Customer, inv.customer_id)),
            "payments": [_payment(p, inv.number) for p in pays]}


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(body: InvoiceIn, db: Session = Depends(get_db), user: User = can_write):
    c = service.resolve_customer(db, body.customer_id, body.customer)
    inv = service.create_invoice(db, c.id, body.amount, user.id, body.order_id, body.issued,
                                 body.due, body.notes)
    log_action(db, user.id, "create", "finance.Invoice", inv.id)
    return _invoice(inv, c)


@router.get("/payments", response_model=list[PaymentOut], dependencies=[can_read])
def list_payments(invoice_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Payment, Invoice.number).join(Invoice, Invoice.id == Payment.invoice_id)
    if invoice_id:
        stmt = stmt.where(Payment.invoice_id == invoice_id)
    return [_payment(p, n) for p, n in db.execute(stmt.order_by(Payment.id.desc()))]


@router.post("/payments", response_model=PaymentOut, status_code=201)
def create_payment(body: PaymentIn, db: Session = Depends(get_db), user: User = can_write):
    p = service.add_payment(db, body.invoice_id, body.amount, body.method, body.date, user.id)
    log_action(db, user.id, "create", "finance.Payment", p.id)
    return _payment(p, service.get_invoice(db, p.invoice_id).number)


@router.get("/expenses", response_model=list[ExpenseOut], dependencies=[can_read])
def list_expenses(category: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Expense)
    if category:
        stmt = stmt.where(Expense.category == category)
    return db.scalars(stmt.order_by(Expense.date.desc(), Expense.id.desc())).all()


@router.post("/expenses", response_model=ExpenseOut, status_code=201)
def create_expense(body: ExpenseIn, db: Session = Depends(get_db), user: User = can_write):
    e = Expense(date=body.date or date.today(), category=body.category, vendor=body.vendor,
                amount=service.money(body.amount), status=body.status, created_by=user.id)
    db.add(e)
    db.commit()
    log_action(db, user.id, "create", "finance.Expense", e.id)
    return e


def _camel(v):
    if isinstance(v, dict):
        return {to_camel(k): _camel(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_camel(x) for x in v]
    return v


def _period(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    """Default: suuliin 6 sar (odoogiin sar orolcono)."""
    end = date_to or date.today()
    start = date_from or (end.replace(day=1) - timedelta(days=150)).replace(day=1)
    if start > end:
        raise UnprocessableError("date_from > date_to")
    return start, end


@router.get("/reports/summary", dependencies=[can_read])
def report_summary(date_from: date | None = None, date_to: date | None = None,
                   db: Session = Depends(get_db)):
    return _camel(service.report(db, *_period(date_from, date_to)))


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# Tatah holboos: brauzer file-g engiin linkeer (Authorization header-gui) tatna.
# Ug token zuvhun ene endpoint-d, DL_MINUTES hugatsaand huchintei (core.deps purpose-tei token-g API-d hulgeehgui).
DL_PURPOSE, DL_MINUTES = "finance-export", 2


def _export_user(dl: str | None = None,
                 cred: HTTPAuthorizationCredentials | None = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    if dl is None:
        user = get_current_user(cred, db)
    else:
        try:
            payload = decode_access_token(dl)
            if payload.get("purpose") != DL_PURPOSE:
                raise ValueError("purpose")
            user = db.get(User, int(payload["sub"]))
        except Exception:  # noqa: BLE001
            raise UnauthorizedError("Tatah holboosiin hugatsaa duussan. Tovchiig dahin darna uu")
        if user is None or not user.is_active:
            raise UnauthorizedError("Hereglegch oldsongui esvel idevhgui")
    if not has_permission(user.role, "finance:read"):
        raise ForbiddenError("Erh hureltsehgui: finance:read")
    return user


@router.post("/reports/export-link")
def report_export_link(date_from: date | None = None, date_to: date | None = None,
                       user: User = can_read):
    """Neg udaagiin (DL_MINUTES) tatah holboos butsaana."""
    start, end = _period(date_from, date_to)
    dl = create_access_token(str(user.id), {"purpose": DL_PURPOSE}, minutes=DL_MINUTES)
    query = urlencode({"date_from": start.isoformat(), "date_to": end.isoformat(), "dl": dl})
    return {"url": f"/api/finance/reports/export?{query}", "expires_in": DL_MINUTES * 60}


@router.get("/reports/export")
def report_export(date_from: date | None = None, date_to: date | None = None,
                  db: Session = Depends(get_db), user: User = Depends(_export_user)):
    """Tailang Excel (.xlsx) file-aar tatah (Bearer token esvel export-link-iin dl)."""
    start, end = _period(date_from, date_to)
    data = export.build_report(db, start, end, user.full_name or user.username)
    log_action(db, user.id, "export", "finance.Report", None,
               {"from": start.isoformat(), "to": end.isoformat()})
    ascii_name = f"finance_report_{start:%Y-%m-%d}_{end:%Y-%m-%d}.xlsx"
    mn_name = f"Санхүүгийн_тайлан_{start:%Y-%m-%d}_{end:%Y-%m-%d}.xlsx"
    return Response(data, media_type=XLSX, headers={
        "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(mn_name)}"})
=======
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permission

from . import service as svc
from .schemas import (ExpenseCreate, ExpenseRead, InvoiceCreate, InvoiceRead, PaymentCreate,
                      PaymentRead)

router = APIRouter(prefix="/api/finance", tags=["Finance"])
read = Depends(require_permission("finance:read"))
write = require_permission("finance:write")

# Frontend (src/api.js) list endpoint-ees Array huleedeg tul Page biš, jagsaalt butsaana.
Limit = Query(1000, ge=1, le=5000)
Offset = Query(0, ge=0)


@router.get("/health")
def health():
    return {"module": "finance", "status": "ok"}


# ---- invoices ----
@router.get("/invoices", response_model=list[InvoiceRead], dependencies=[read])
def list_invoices(customer_id: int | None = None, order_id: int | None = None,
                  limit: int = Limit, offset: int = Offset, db: Session = Depends(get_db)):
    items = svc.list_invoices(db, customer_id, order_id, limit, offset)
    names = svc.customer_names(db, items)
    return [svc.invoice_dict(i, names) for i in items]


@router.post("/invoices", response_model=InvoiceRead, status_code=201)
def create_invoice(body: InvoiceCreate, db: Session = Depends(get_db), user=Depends(write)):
    inv = svc.create_invoice(db, body, user.id)
    return svc.invoice_dict(inv, svc.customer_names(db, [inv]))


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead, dependencies=[read])
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = svc.get_invoice(db, invoice_id)
    return svc.invoice_dict(inv, svc.customer_names(db, [inv]))


# ---- payments ----
@router.get("/payments", response_model=list[PaymentRead], dependencies=[read])
def list_payments(invoice_id: int | None = None, limit: int = Limit, offset: int = Offset,
                  db: Session = Depends(get_db)):
    return [{"id": p.id, "invoiceId": p.invoice_id, "date": p.date, "amount": p.amount,
             "method": p.method} for p in svc.list_payments(db, invoice_id, limit, offset)]


@router.post("/payments", response_model=PaymentRead, status_code=201)
def create_payment(body: PaymentCreate, db: Session = Depends(get_db), user=Depends(write)):
    p = svc.create_payment(db, body, user.id)
    return {"id": p.id, "invoiceId": p.invoice_id, "date": p.date, "amount": p.amount,
            "method": p.method}


# ---- expenses ----
@router.get("/expenses", response_model=list[ExpenseRead], dependencies=[read])
def list_expenses(category: str | None = None, status: str | None = None,
                  limit: int = Limit, offset: int = Offset, db: Session = Depends(get_db)):
    return svc.list_expenses(db, category, status, limit, offset)


@router.post("/expenses", response_model=ExpenseRead, status_code=201)
def create_expense(body: ExpenseCreate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.create_expense(db, body, user.id)
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
