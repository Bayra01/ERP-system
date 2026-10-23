from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permission
from core.pagination import Page, PageParams

from . import service as svc
from .models import Customer, Location, Product
from .schemas import (CustomerCreate, CustomerRead, CustomerUpdate, LocationCreate, LocationRead,
                      LocationType, LocationUpdate, ProductCreate, ProductRead, ProductUpdate)

router = APIRouter(prefix="/api/masterdata", tags=["Master data"])
read = Depends(require_permission("masterdata:read"))
write = require_permission("masterdata:write")


def _page(res, params):
    items, total = res
    return Page(items=items, total=total, page=params.page, size=params.size)


# ---------- Customers
@router.get("/customers", response_model=Page[CustomerRead], dependencies=[read])
def list_customers(params: PageParams = Depends(), q: str | None = None,
                   is_active: bool | None = None, db: Session = Depends(get_db)):
    return _page(svc.list_items(db, Customer, params, q,
                                (Customer.name, Customer.code, Customer.phone), is_active), params)


@router.post("/customers", response_model=CustomerRead, status_code=201)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.create_item(db, Customer, body, "code", user.id)


@router.get("/customers/{item_id}", response_model=CustomerRead, dependencies=[read])
def get_customer(item_id: int, db: Session = Depends(get_db)):
    return svc.get_item(db, Customer, item_id)


@router.patch("/customers/{item_id}", response_model=CustomerRead)
def update_customer(item_id: int, body: CustomerUpdate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.update_item(db, Customer, item_id, body, user.id)


@router.delete("/customers/{item_id}", status_code=204)
def delete_customer(item_id: int, db: Session = Depends(get_db), user=Depends(write)):
    svc.delete_item(db, Customer, item_id, user.id)


# ---------- Products
@router.get("/products", response_model=Page[ProductRead], dependencies=[read])
def list_products(params: PageParams = Depends(), q: str | None = None,
                  is_active: bool | None = None, db: Session = Depends(get_db)):
    return _page(svc.list_items(db, Product, params, q, (Product.name, Product.sku), is_active), params)


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(body: ProductCreate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.create_item(db, Product, body, "sku", user.id)


@router.get("/products/{item_id}", response_model=ProductRead, dependencies=[read])
def get_product(item_id: int, db: Session = Depends(get_db)):
    return svc.get_item(db, Product, item_id)


@router.patch("/products/{item_id}", response_model=ProductRead)
def update_product(item_id: int, body: ProductUpdate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.update_item(db, Product, item_id, body, user.id)


@router.delete("/products/{item_id}", status_code=204)
def delete_product(item_id: int, db: Session = Depends(get_db), user=Depends(write)):
    svc.delete_item(db, Product, item_id, user.id)


# ---------- Locations
@router.get("/locations", response_model=Page[LocationRead], dependencies=[read])
def list_locations(params: PageParams = Depends(), q: str | None = None,
                   type: LocationType | None = None, customer_id: int | None = Query(None),
                   is_active: bool | None = None, db: Session = Depends(get_db)):
    extra = []
    if type:
        extra.append(Location.type == type.value)
    if customer_id is not None:
        extra.append(Location.customer_id == customer_id)
    return _page(svc.list_items(db, Location, params, q, (Location.name, Location.address),
                                is_active, extra), params)


@router.post("/locations", response_model=LocationRead, status_code=201)
def create_location(body: LocationCreate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.create_item(db, Location, body, None, user.id)


@router.get("/locations/{item_id}", response_model=LocationRead, dependencies=[read])
def get_location(item_id: int, db: Session = Depends(get_db)):
    return svc.get_item(db, Location, item_id)


@router.patch("/locations/{item_id}", response_model=LocationRead)
def update_location(item_id: int, body: LocationUpdate, db: Session = Depends(get_db), user=Depends(write)):
    return svc.update_item(db, Location, item_id, body, user.id)


@router.delete("/locations/{item_id}", status_code=204)
def delete_location(item_id: int, db: Session = Depends(get_db), user=Depends(write)):
    svc.delete_item(db, Location, item_id, user.id)
