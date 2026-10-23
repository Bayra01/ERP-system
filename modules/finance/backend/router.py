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
