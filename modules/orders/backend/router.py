<<<<<<< HEAD
"""/api/orders"""
=======
from datetime import datetime

>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
<<<<<<< HEAD
from core.deps import require_permission
from core.pagination import Page, PageParams, paginate
from modules.auth.backend.models import User

from . import handlers  # noqa: F401  event handler burtgene
from . import service
from .schemas import OrderCreate, OrderDetail, OrderOut, OrderUpdate, Status, StatusChange

router = APIRouter(prefix="/api/orders", tags=["Orders"])
can_read = Depends(require_permission("orders:read"))
can_write = Depends(require_permission("orders:write"))


@router.get("", response_model=Page[OrderOut], dependencies=[can_read])
def list_orders(params: PageParams = Depends(), status: Status | None = None,
                q: str | None = None, customer_id: int | None = None,
                db: Session = Depends(get_db)):
    items, total = paginate(db, service.list_stmt(status, q, customer_id), params)
    return {"items": items, "total": total, "page": params.page, "size": params.size}


@router.get("/{order_id}", response_model=OrderDetail, dependencies=[can_read])
def get_order(order_id: int, db: Session = Depends(get_db)):
    return service.get_order(db, order_id)


@router.post("", response_model=OrderDetail, status_code=201)
def create_order(body: OrderCreate, db: Session = Depends(get_db), user: User = can_write):
    return service.create_order(db, body, user)


@router.patch("/{order_id}", response_model=OrderDetail)
def update_order(order_id: int, body: OrderUpdate, db: Session = Depends(get_db),
                 user: User = can_write):
    return service.update_order(db, service.get_order(db, order_id), body, user)


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db), user: User = can_write):
    service.delete_order(db, service.get_order(db, order_id), user)


@router.post("/{order_id}/status", response_model=OrderDetail)
def change_status(order_id: int, body: StatusChange, db: Session = Depends(get_db),
                  user: User = can_read):
    # Shiljilt burt tusdaa erh (service.TRANSITION_PERMISSION) shalgagdana.
    return service.change_status(db, service.get_order(db, order_id), body.to, user, body.note)
=======
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
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
