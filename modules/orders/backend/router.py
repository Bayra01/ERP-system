from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user, require_permission
from core.pagination import Page, PageParams

from . import service as svc
from .schemas import (OrderCreate, OrderRead, OrderStatus, OrderSummary, OrderUpdate,
                      StatusChange)

router = APIRouter(prefix="/api/orders", tags=["Orders"])
read = Depends(require_permission("orders:read"))
write = require_permission("orders:write")


@router.get("/health")
def health():
    return {"module": "orders", "status": "ok"}


@router.get("", response_model=Page[OrderSummary], dependencies=[read])
def list_orders(params: PageParams = Depends(), status: OrderStatus | None = None,
                customer_id: int | None = None, q: str | None = None,
                date_from: datetime | None = None, date_to: datetime | None = None,
                db: Session = Depends(get_db)):
    items, total = svc.list_orders(db, params, status.value if status else None,
                                   customer_id, q, date_from, date_to)
    return Page(items=items, total=total, page=params.page, size=params.size)


@router.post("", response_model=OrderRead, status_code=201)
def create_order(body: OrderCreate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.create_order(db, body, user.id)


@router.get("/{order_id}", response_model=OrderRead, dependencies=[read])
def get_order(order_id: int, db: Session = Depends(get_db)):
    return svc.get_order(db, order_id)


@router.patch("/{order_id}", response_model=OrderRead)
def update_order(order_id: int, body: OrderUpdate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.update_order(db, order_id, body, user.id)


@router.delete("/{order_id}", status_code=204)
def delete_draft(order_id: int, db: Session = Depends(get_db), user=Depends(write)):
    svc.delete_draft(db, order_id, user.id)


@router.post("/{order_id}/status", response_model=OrderRead)
def change_status(order_id: int, body: StatusChange, db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    return svc.change_status(db, order_id, body.to.value, user.role, user.id, body.note)
