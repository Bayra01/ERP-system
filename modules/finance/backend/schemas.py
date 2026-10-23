"""Frontend (modules/finance/frontend/README.md) huleej avdag shape: camelCase, dun = number."""
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class Method(str, Enum):
    transfer = "transfer"
    cash = "cash"
    card = "card"


class ExpenseStatus(str, Enum):
    paid = "paid"
    pending = "pending"


class InvoiceCreate(BaseModel):
    # customer (ner) esvel customer_id-nii neg n zaaval. Ner oldohgui bol shine kharitsagch uusgene.
    customer: str | None = Field(default=None, min_length=1, max_length=200)
    customer_id: int | None = None
    issued: date
    due: date
    amount: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    notes: str | None = None


class InvoiceRead(BaseModel):
    id: int
    number: str | None
    customer: str
    customerId: int
    orderId: int | None
    issued: date
    due: date
    amount: float
    paid: float


class PaymentCreate(BaseModel):
    invoiceId: int
    date: date
    amount: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    method: Method


class PaymentRead(BaseModel):
    id: int
    invoiceId: int
    date: date
    amount: float
    method: str


class ExpenseCreate(BaseModel):
    date: date
    category: str = Field(min_length=1, max_length=80)
    vendor: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    status: ExpenseStatus = ExpenseStatus.paid


class ExpenseRead(BaseModel):
    id: int
    date: date
    category: str
    vendor: str
    amount: float
    status: str
