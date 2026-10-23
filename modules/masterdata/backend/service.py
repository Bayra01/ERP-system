"""Customers / Products / Locations-iin CRUD. Ustgal = soft delete."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from core.audit import log_action
from core.exceptions import ConflictError, NotFoundError
from core.mixins import utcnow
from core.pagination import PageParams, paginate

from .models import Customer, Location, Product

ENTITY = {Customer: "masterdata.Customer", Product: "masterdata.Product", Location: "masterdata.Location"}


def _dump(data) -> dict:
    d = data.model_dump(exclude_unset=True)
    return {k: (v.value if hasattr(v, "value") else v) for k, v in d.items()}


def list_items(db: Session, model, params: PageParams, q: str | None = None,
               search_cols=(), is_active: bool | None = None, extra_filters=()):
    stmt = select(model).where(model.deleted_at.is_(None))
    if q:
        stmt = stmt.where(or_(*[c.ilike(f"%{q}%") for c in search_cols]))
    if is_active is not None:
        stmt = stmt.where(model.is_active == is_active)
    for f in extra_filters:
        stmt = stmt.where(f)
    return paginate(db, stmt.order_by(model.id), params)


def get_item(db: Session, model, item_id: int):
    obj = db.get(model, item_id)
    if obj is None or obj.deleted_at is not None:
        raise NotFoundError(f"{model.__name__} oldsongui")
    return obj


def _check_customer(db: Session, customer_id: int | None) -> None:
    if customer_id is not None:
        get_item(db, Customer, customer_id)


def create_item(db: Session, model, data, unique_field: str | None = None, actor_id: int | None = None):
    values = _dump(data)
    if unique_field:
        exists = db.scalar(select(model.id).where(getattr(model, unique_field) == values[unique_field]))
        if exists:
            raise ConflictError(f"{unique_field} '{values[unique_field]}' davhtsaj baina")
    if model is Location:
        _check_customer(db, values.get("customer_id"))
    obj = model(**values)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, actor_id, "create", ENTITY[model], obj.id)
    return obj


def update_item(db: Session, model, item_id: int, data, actor_id: int | None = None):
    obj = get_item(db, model, item_id)
    values = _dump(data)
    if model is Location:
        _check_customer(db, values.get("customer_id"))
    for k, v in values.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    log_action(db, actor_id, "update", ENTITY[model], obj.id, {"fields": list(values)})
    return obj


def delete_item(db: Session, model, item_id: int, actor_id: int | None = None) -> None:
    obj = get_item(db, model, item_id)
    if model is Customer:
        used = db.scalar(select(Location.id).where(Location.customer_id == obj.id,
                                                   Location.deleted_at.is_(None)).limit(1))
        if used:
            raise ConflictError("Hariltsagchtai holbootoi hayag baina, ehleed tedgeeriig ustgana uu")
    obj.deleted_at = utcnow()
    obj.is_active = False
    db.commit()
    log_action(db, actor_id, "delete", ENTITY[model], obj.id)
