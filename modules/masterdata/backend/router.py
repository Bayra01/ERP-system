"""/api/masterdata - Customers, Products, Locations. Ustgal = soft delete."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from core.audit import log_action
from core.database import get_db
from core.deps import require_permission
from core.exceptions import ConflictError, NotFoundError, UnprocessableError
from core.mixins import utcnow
from core.pagination import Page, PageParams, paginate
from modules.auth.backend.models import User

from .models import Customer, Location, Product
from .schemas import (CustomerCreate, CustomerOut, CustomerUpdate, LocationCreate, LocationOut,
                      LocationUpdate, ProductCreate, ProductOut, ProductUpdate)

router = APIRouter(prefix="/api/masterdata", tags=["Masterdata"])
can_read = Depends(require_permission("masterdata:read"))
can_write = Depends(require_permission("masterdata:write"))


def _get(db: Session, model, obj_id: int):
    obj = db.get(model, obj_id)
    if obj is None or obj.deleted_at is not None:
        raise NotFoundError(f"{model.__name__} #{obj_id} oldsongui")
    return obj


def _unique(db: Session, model, field: str, value: str | None, exclude_id: int | None = None):
    if value is None:
        return
    stmt = select(model.id).where(getattr(model, field) == value)
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.scalar(stmt):
        raise ConflictError(f"{field} '{value}' burtgeltei baina")


def _apply(obj, data: dict):
    for k, v in data.items():
        setattr(obj, k, v)


def _list(db: Session, model, params: PageParams, q: str | None, is_active: bool | None,
          search: tuple, *where):
    stmt = select(model).where(model.deleted_at.is_(None), *where)
    if q:
        stmt = stmt.where(or_(*(c.ilike(f"%{q}%") for c in search)))
    if is_active is not None:
        stmt = stmt.where(model.is_active.is_(is_active))
    items, total = paginate(db, stmt.order_by(model.id), params)
    return {"items": items, "total": total, "page": params.page, "size": params.size}


def _delete(db: Session, model, obj_id: int, user: User, entity: str):
    obj = _get(db, model, obj_id)
    obj.deleted_at = utcnow()
    obj.is_active = False
    db.commit()
    log_action(db, user.id, "delete", entity, obj.id)


# ---------------- Customers
@router.get("/customers", response_model=Page[CustomerOut], dependencies=[can_read])
def list_customers(params: PageParams = Depends(), q: str | None = None,
                   is_active: bool | None = None, db: Session = Depends(get_db)):
    return _list(db, Customer, params, q, is_active, (Customer.name, Customer.code, Customer.phone))


@router.get("/customers/{obj_id}", response_model=CustomerOut, dependencies=[can_read])
def get_customer(obj_id: int, db: Session = Depends(get_db)):
    return _get(db, Customer, obj_id)


@router.post("/customers", response_model=CustomerOut, status_code=201)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db), user: User = can_write):
    _unique(db, Customer, "code", body.code)
    obj = Customer(**body.model_dump(exclude={"code"}), code=body.code or "")
    db.add(obj)
    db.flush()
    if not obj.code:
        obj.code = f"C-{obj.id}"
    db.commit()
    log_action(db, user.id, "create", "masterdata.Customer", obj.id)
    return obj


@router.patch("/customers/{obj_id}", response_model=CustomerOut)
def update_customer(obj_id: int, body: CustomerUpdate, db: Session = Depends(get_db),
                    user: User = can_write):
    obj = _get(db, Customer, obj_id)
    data = body.model_dump(exclude_unset=True)
    _unique(db, Customer, "code", data.get("code"), obj.id)
    _apply(obj, data)
    db.commit()
    log_action(db, user.id, "update", "masterdata.Customer", obj.id, {"fields": sorted(data)})
    return obj


@router.delete("/customers/{obj_id}", status_code=204)
def delete_customer(obj_id: int, db: Session = Depends(get_db), user: User = can_write):
    _delete(db, Customer, obj_id, user, "masterdata.Customer")


# ---------------- Products
@router.get("/products", response_model=Page[ProductOut], dependencies=[can_read])
def list_products(params: PageParams = Depends(), q: str | None = None,
                  is_active: bool | None = None, db: Session = Depends(get_db)):
    return _list(db, Product, params, q, is_active, (Product.name, Product.sku))


@router.get("/products/{obj_id}", response_model=ProductOut, dependencies=[can_read])
def get_product(obj_id: int, db: Session = Depends(get_db)):
    return _get(db, Product, obj_id)


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(body: ProductCreate, db: Session = Depends(get_db), user: User = can_write):
    _unique(db, Product, "sku", body.sku)
    obj = Product(**body.model_dump())
    db.add(obj)
    db.commit()
    log_action(db, user.id, "create", "masterdata.Product", obj.id)
    return obj


@router.patch("/products/{obj_id}", response_model=ProductOut)
def update_product(obj_id: int, body: ProductUpdate, db: Session = Depends(get_db),
                   user: User = can_write):
    obj = _get(db, Product, obj_id)
    data = body.model_dump(exclude_unset=True)
    _unique(db, Product, "sku", data.get("sku"), obj.id)
    _apply(obj, data)
    db.commit()
    log_action(db, user.id, "update", "masterdata.Product", obj.id, {"fields": sorted(data)})
    return obj


@router.delete("/products/{obj_id}", status_code=204)
def delete_product(obj_id: int, db: Session = Depends(get_db), user: User = can_write):
    _delete(db, Product, obj_id, user, "masterdata.Product")


# ---------------- Locations
def _check_customer(db: Session, customer_id: int | None):
    if customer_id is not None:
        try:
            _get(db, Customer, customer_id)
        except NotFoundError:
            raise UnprocessableError(f"Harilcagch #{customer_id} oldsongui")


@router.get("/locations", response_model=Page[LocationOut], dependencies=[can_read])
def list_locations(params: PageParams = Depends(), q: str | None = None,
                   is_active: bool | None = None, type: str | None = None,
                   customer_id: int | None = Query(None), db: Session = Depends(get_db)):
    where = []
    if type:
        where.append(Location.type == type)
    if customer_id is not None:
        where.append(Location.customer_id == customer_id)
    return _list(db, Location, params, q, is_active, (Location.name, Location.address), *where)


@router.get("/locations/{obj_id}", response_model=LocationOut, dependencies=[can_read])
def get_location(obj_id: int, db: Session = Depends(get_db)):
    return _get(db, Location, obj_id)


@router.post("/locations", response_model=LocationOut, status_code=201)
def create_location(body: LocationCreate, db: Session = Depends(get_db), user: User = can_write):
    _check_customer(db, body.customer_id)
    obj = Location(**body.model_dump())
    db.add(obj)
    db.commit()
    log_action(db, user.id, "create", "masterdata.Location", obj.id)
    return obj


@router.patch("/locations/{obj_id}", response_model=LocationOut)
def update_location(obj_id: int, body: LocationUpdate, db: Session = Depends(get_db),
                    user: User = can_write):
    obj = _get(db, Location, obj_id)
    data = body.model_dump(exclude_unset=True)
    _check_customer(db, data.get("customer_id"))
    _apply(obj, data)
    db.commit()
    log_action(db, user.id, "update", "masterdata.Location", obj.id, {"fields": sorted(data)})
    return obj


@router.delete("/locations/{obj_id}", status_code=204)
def delete_location(obj_id: int, db: Session = Depends(get_db), user: User = can_write):
    _delete(db, Location, obj_id, user, "masterdata.Location")
