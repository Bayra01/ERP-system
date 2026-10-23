from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user, require_permission
from core.pagination import Page, PageParams, paginate

from . import service
from .models import User
from .schemas import LoginRequest, TokenResponse, UserCreate, UserRead, UserUpdate

router = APIRouter()
admin_only = require_permission("users:manage")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    return TokenResponse(access_token=service.authenticate(db, body.username, body.password))


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=Page[UserRead])
def list_users(params: PageParams = Depends(), db: Session = Depends(get_db),
               _: User = Depends(admin_only)):
    items, total = paginate(db, select(User).order_by(User.id), params)
    return Page(items=items, total=total, page=params.page, size=params.size)


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), actor: User = Depends(admin_only)):
    return service.create_user(db, body, actor.id)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db),
                actor: User = Depends(admin_only)):
    return service.update_user(db, user_id, body, actor.id)
