<<<<<<< HEAD
"""/api/warehouse"""
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from core.audit import log_action
from core.database import get_db
from core.deps import require_permission
from core.exceptions import NotFoundError
from core.pagination import Page, PageParams
from modules.auth.backend.models import User
from modules.masterdata.backend.models import Location, Product

from . import handlers  # noqa: F401  event handler burtgene
from . import service
from .models import Movement, Reservation, Stock
from .schemas import (MovementIn, MovementOut, ReservationOut, StockOut, StockUpdate, Summary,
                      TransferIn, WarehouseOut)

router = APIRouter(prefix="/api/warehouse", tags=["Warehouse"])
can_read = Depends(require_permission("warehouse:read"))
can_write = Depends(require_permission("warehouse:write"))

_status = case((Stock.on_hand <= 0, "out"),
               (Stock.on_hand < Stock.min_level, "low"), else_="ok")


def _page(db: Session, stmt, params: PageParams, row_fn):
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.limit(params.size).offset((params.page - 1) * params.size)).all()
    return {"items": [row_fn(r) for r in rows], "total": total,
            "page": params.page, "size": params.size}


def _stock_row(r) -> dict:
    st, loc, p, status = r
    return {"id": st.id, "location_id": st.location_id, "location_name": loc.name,
            "product_id": st.product_id, "sku": p.sku, "product_name": p.name, "unit": p.unit,
            "on_hand": st.on_hand, "reserved": st.reserved, "available": st.available,
            "min_level": st.min_level, "status": status, "updated_at": st.updated_at}


def _move_row(r) -> dict:
    mv, loc, p = r
    return {**{c: getattr(mv, c) for c in ("id", "location_id", "product_id", "type", "quantity",
                                            "balance_after", "ref_type", "ref_id", "note",
                                            "user_id", "created_at")},
            "location_name": loc.name, "sku": p.sku, "product_name": p.name}


@router.get("/warehouses", response_model=list[WarehouseOut], dependencies=[can_read])
def warehouses(db: Session = Depends(get_db)):
    return db.scalars(select(Location).where(Location.type == "warehouse",
                                             Location.deleted_at.is_(None))
                      .order_by(Location.id)).all()


@router.get("/stock", response_model=Page[StockOut], dependencies=[can_read])
def list_stock(params: PageParams = Depends(), location_id: int | None = None,
               product_id: int | None = None, q: str | None = None,
               status: Literal["ok", "low", "out"] | None = None, db: Session = Depends(get_db)):
    stmt = (select(Stock, Location, Product, _status)
            .join(Location, Location.id == Stock.location_id)
            .join(Product, Product.id == Stock.product_id)
            .where(Product.deleted_at.is_(None), Location.deleted_at.is_(None)))
    if location_id:
        stmt = stmt.where(Stock.location_id == location_id)
    if product_id:
        stmt = stmt.where(Stock.product_id == product_id)
    if q:
        stmt = stmt.where(or_(Product.name.ilike(f"%{q}%"), Product.sku.ilike(f"%{q}%")))
    if status:
        stmt = stmt.where(_status == status)
    return _page(db, stmt.order_by(Product.sku, Location.id), params, _stock_row)


@router.get("/summary", response_model=Summary, dependencies=[can_read])
def summary(location_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(func.count(func.distinct(Stock.product_id)), func.coalesce(func.sum(Stock.on_hand), 0),
                  func.coalesce(func.sum(Stock.reserved), 0),
                  func.coalesce(func.sum(case((_status == "low", 1), else_=0)), 0),
                  func.coalesce(func.sum(case((_status == "out", 1), else_=0)), 0))
    if location_id:
        stmt = stmt.where(Stock.location_id == location_id)
    products, on_hand, reserved, low, out = db.execute(stmt).one()
    return Summary(products=products, total_on_hand=on_hand, total_reserved=reserved,
                   low=low, out=out)


@router.patch("/stock/{stock_id}", response_model=StockOut)
def update_stock(stock_id: int, body: StockUpdate, db: Session = Depends(get_db),
                 user: User = can_write):
    st = db.get(Stock, stock_id)
    if st is None:
        raise NotFoundError("Uldegdliin mor oldsongui")
    st.min_level = body.min_level
    db.commit()
    log_action(db, user.id, "update", "warehouse.Stock", st.id, {"min_level": float(body.min_level)})
    row = db.execute(select(Stock, Location, Product, _status)
                     .join(Location, Location.id == Stock.location_id)
                     .join(Product, Product.id == Stock.product_id)
                     .where(Stock.id == st.id)).one()
    return _stock_row(row)


@router.get("/movements", response_model=Page[MovementOut], dependencies=[can_read])
def list_movements(params: PageParams = Depends(), location_id: int | None = None,
                   product_id: int | None = None, type: str | None = None,
                   db: Session = Depends(get_db)):
    stmt = (select(Movement, Location, Product)
            .join(Location, Location.id == Movement.location_id)
            .join(Product, Product.id == Movement.product_id))
    if location_id:
        stmt = stmt.where(Movement.location_id == location_id)
    if product_id:
        stmt = stmt.where(Movement.product_id == product_id)
    if type:
        stmt = stmt.where(Movement.type == type)
    return _page(db, stmt.order_by(Movement.id.desc()), params, _move_row)


@router.post("/movements", response_model=MovementOut, status_code=201)
def create_movement(body: MovementIn, db: Session = Depends(get_db), user: User = can_write):
    mv = service.move(db, body.location_id, body.product_id, body.type, body.quantity,
                      user.id, body.note)
    log_action(db, user.id, body.type, "warehouse.Movement", mv.id)
    return _move_row((mv, db.get(Location, mv.location_id), db.get(Product, mv.product_id)))


@router.post("/transfers", status_code=204)
def create_transfer(body: TransferIn, db: Session = Depends(get_db), user: User = can_write):
    service.transfer(db, body.from_location_id, body.to_location_id, body.product_id,
                     body.quantity, user.id, body.note)
    log_action(db, user.id, "transfer", "warehouse.Movement", None, body.model_dump(mode="json"))


@router.get("/reservations", response_model=list[ReservationOut], dependencies=[can_read])
def list_reservations(order_id: int | None = None, status: str | None = None,
                      db: Session = Depends(get_db)):
    stmt = select(Reservation)
    if order_id:
        stmt = stmt.where(Reservation.order_id == order_id)
    if status:
        stmt = stmt.where(Reservation.status == status)
    return [ReservationOut.model_validate(r, from_attributes=True)
            for r in db.scalars(stmt.order_by(Reservation.id.desc()).limit(500))]


@router.post("/orders/{order_id}/reserve", response_model=list[ReservationOut])
def retry_reserve(order_id: int, db: Session = Depends(get_db), user: User = can_write):
    rows = service.retry_short(db, order_id)
    log_action(db, user.id, "reserve", "warehouse.Reservation", order_id)
    return [ReservationOut.model_validate(r, from_attributes=True) for r in rows]
=======
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
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
