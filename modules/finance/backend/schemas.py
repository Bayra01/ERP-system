<<<<<<< HEAD
"""Frontend-iin shape: talbaruud camelCase, dun = number."""
import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class InvoiceIn(Camel):
    customer: str | None = Field(None, max_length=200)  # ner; oldohgui bol shine harilcagch
    customer_id: int | None = None
    order_id: int | None = None
    issued: dt.date | None = None
    due: dt.date | None = None
    amount: float = Field(gt=0)
    notes: str | None = None


class PaymentIn(Camel):
    invoice_id: int
    date: dt.date | None = None
    amount: float = Field(gt=0)
    method: Literal["bank", "cash", "card"] = "bank"


class ExpenseIn(Camel):
    date: dt.date | None = None
    category: str = Field(min_length=1, max_length=80)
    vendor: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    status: Literal["pending", "paid"] = "pending"


class PaymentOut(Camel):
    id: int
    invoice_id: int
    invoice_number: str | None
    date: dt.date
=======
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
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    amount: float
    method: str


<<<<<<< HEAD
class InvoiceOut(Camel):
    id: int
    number: str | None
    customer: str
    customer_id: int
    order_id: int | None
    issued: dt.date
    due: dt.date
    amount: float
    paid: float
    balance: float
    status: Literal["paid", "partial", "unpaid", "overdue"]
    notes: str | None


class InvoiceDetail(InvoiceOut):
    payments: list[PaymentOut] = []


class ExpenseOut(Camel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: dt.date
=======
class ExpenseCreate(BaseModel):
    date: date
    category: str = Field(min_length=1, max_length=80)
    vendor: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    status: ExpenseStatus = ExpenseStatus.paid


class ExpenseRead(BaseModel):
    id: int
    date: date
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
    category: str
    vendor: str
    amount: float
    status: str
