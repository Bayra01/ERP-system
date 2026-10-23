from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permission
from core.pagination import Page, PageParams

from . import service as svc
from .schemas import (AdjustIn, AvailabilityRead, IssueIn, MinLevelUpdate, MovementRead, ReceiptIn,
                      ReservationRead, StockRead, TransferIn)

router = APIRouter(prefix="/api/warehouse", tags=["Warehouse"])
read = Depends(require_permission("warehouse:read"))
write = require_permission("warehouse:write")


def _page(res, params):
    items, total = res
    return Page(items=items, total=total, page=params.page, size=params.size)


@router.get("/health")
def health():
    return {"module": "warehouse", "status": "ok"}


@router.get("/stock", response_model=Page[StockRead], dependencies=[read])
def list_stock(params: PageParams = Depends(), location_id: int | None = None,
               product_id: int | None = None, low_only: bool = False, db: Session = Depends(get_db)):
    return _page(svc.list_stock(db, params, location_id, product_id, low_only), params)


@router.patch("/stock/{stock_id}", response_model=StockRead)
def set_min_level(stock_id: int, body: MinLevelUpdate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.set_min_level(db, stock_id, body.min_level, user.id)


@router.get("/availability/{product_id}", response_model=AvailabilityRead, dependencies=[read])
def availability(product_id: int, db: Session = Depends(get_db)):
    return svc.availability(db, product_id)


@router.get("/movements", response_model=Page[MovementRead], dependencies=[read])
def list_movements(params: PageParams = Depends(), location_id: int | None = None,
                   product_id: int | None = None, type: str | None = None,
                   ref_type: str | None = None, ref_id: int | None = None, db: Session = Depends(get_db)):
    return _page(svc.list_movements(db, params, location_id, product_id, type, ref_type, ref_id), params)


@router.post("/receipts", response_model=MovementRead, status_code=201)
def receipt(body: ReceiptIn, db: Session = Depends(get_db), user=Depends(write)):
    return svc.receive(db, body, user.id)


@router.post("/issues", response_model=MovementRead, status_code=201)
def issue(body: IssueIn, db: Session = Depends(get_db), user=Depends(write)):
    return svc.issue(db, body, user.id)


@router.post("/adjustments", response_model=MovementRead, status_code=201)
def adjustment(body: AdjustIn, db: Session = Depends(get_db), user=Depends(write)):
    return svc.adjust(db, body, user.id)


@router.post("/transfers", response_model=list[MovementRead], status_code=201)
def transfer(body: TransferIn, db: Session = Depends(get_db), user=Depends(write)):
    return svc.transfer(db, body, user.id)


@router.get("/orders/{order_id}/reservations", response_model=list[ReservationRead], dependencies=[read])
def order_reservations(order_id: int, db: Session = Depends(get_db)):
    return svc.order_reservations(db, order_id)


@router.post("/orders/{order_id}/reserve", response_model=list[ReservationRead])
def retry_reserve(order_id: int, db: Session = Depends(get_db), user=Depends(write)):
    """Uldegdel nemegdsenii daraa 'short' reserve-g dahin hiih."""
    short = svc.retry_reserve(db, order_id)
    if short:
        from core import events
        events.publish("stock.shortage", {"order_id": order_id, "shortages": short, "stage": "retry"})
    return svc.order_reservations(db, order_id)
