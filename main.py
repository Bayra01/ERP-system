import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

# Project-oos gadnaas ajilluulbal ch import ajillana.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import get_settings  # noqa: E402
from core.database import Base, SessionLocal, engine  # noqa: E402
from core.exceptions import register_exception_handlers  # noqa: E402
from core.registry import import_all_models  # noqa: E402
from modules.auth.backend.router import router as auth_router  # noqa: E402
from modules.auth.backend.service import ensure_first_admin  # noqa: E402
from modules.finance.backend.router import router as finance_router  # noqa: E402
from modules.notifications.backend.router import router as notifications_router  # noqa: E402
from modules.masterdata.backend.router import router as masterdata_router  # noqa: E402
from modules.orders.backend.router import router as orders_router  # noqa: E402
from modules.routing.backend.router import router as routing_router  # noqa: E402
from modules.transport.backend.router import router as transport_router  # noqa: E402
from modules.warehouse.backend.router import router as warehouse_router  # noqa: E402

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    import_all_models()
    # Dev tulhuur: sqlite deer table-g avtomataar uusgene. Prod deer `alembic upgrade head`.
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_first_admin(db)
    yield


app = FastAPI(title=settings.APP_NAME, description="Logistics ERP system backend",
              version="1.0.0", lifespan=lifespan)
register_exception_handlers(app)

# Modul burt router uuriin prefix-tei (/api/<modul>) tul end prefix nemehgui.
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
for r in (masterdata_router, orders_router, warehouse_router, transport_router,
          routing_router, finance_router, notifications_router):
    app.include_router(r)


@app.get("/")
def home():
    return {"message": "Logistics ERP API is running", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
