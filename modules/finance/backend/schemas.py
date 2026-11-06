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
    amount: float
    method: str


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
    category: str
    vendor: str
    amount: float
    status: str
