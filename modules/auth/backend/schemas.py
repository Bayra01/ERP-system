<<<<<<< HEAD
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from core.permissions import ROLE_PERMISSIONS, Role, allowed_modules

Module = Literal["orders", "warehouse", "transport", "routing", "finance", "notifications"]


class LoginIn(BaseModel):
    username: str
    password: str
    module: Module | None = None  # /login/<modul> hudsaas: erhgui bol 403
    # Nevtreh huudasnii songolt: admin = zuvhun admin, user = admin bish ajiltan. None = shalgahgui (API, Swagger)
    login_as: Literal["admin", "user"] | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: Role
    is_active: bool
    pending: bool = False
    created_at: datetime | None = None

    @computed_field  # frontend tovch haruulah/nuuhad ashiglana
    @property
    def permissions(self) -> list[str]:
        return sorted(ROLE_PERMISSIONS.get(self.role, set()))

    @computed_field
    @property
    def modules(self) -> list[str]:
        return allowed_modules(self.role)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
=======
from pydantic import BaseModel, ConfigDict, Field

from core.permissions import Role


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
<<<<<<< HEAD
    full_name: str = Field("", max_length=120)
    password: str = Field(min_length=6)
    role: Role = Role.DISPATCHER
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=120)
    password: str | None = Field(None, min_length=6)
    role: Role | None = None
    is_active: bool | None = None


SelfRole = Literal["user", "dispatcher", "warehouse", "driver", "accountant"]  # admin-aar burtguulehgui


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.\-]+$")
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=6, max_length=128)
    role: SelfRole = "user"  # husej bui ureg; admin batlahdaa uurchilj bolno


class ApproveIn(BaseModel):
    role: SelfRole | Role | None = None  # hooson bol husesen uureg hevendee


class MeUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    user_name: str | None = None
    action: str
    entity: str
    entity_id: str | None
    detail: dict | None
    created_at: datetime
=======
    password: str = Field(min_length=8, max_length=128)
    full_name: str = ""
    role: Role = Role.DISPATCHER


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
