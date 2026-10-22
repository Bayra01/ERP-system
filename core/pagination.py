from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=200),
    ):
        self.page, self.size = page, size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


def paginate(db: Session, stmt, params: PageParams) -> tuple[list, int]:
    """stmt = select(Model).where(...). (items, total) butsaana."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.limit(params.size).offset((params.page - 1) * params.size)).all()
    return list(items), total
