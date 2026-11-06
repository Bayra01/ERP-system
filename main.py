import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
<<<<<<< HEAD
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# Project-oos gadnaas ajilluulbal ch import ajillana.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
=======

# Project-oos gadnaas ajilluulbal ch import ajillana.
sys.path.insert(0, str(Path(__file__).resolve().parent))
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4

from core.config import get_settings  # noqa: E402
from core.database import Base, SessionLocal, engine  # noqa: E402
from core.exceptions import register_exception_handlers  # noqa: E402
<<<<<<< HEAD
from core.permissions import MODULE_PERMISSIONS  # noqa: E402
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
from core.registry import import_all_models  # noqa: E402
from modules.auth.backend.router import router as auth_router  # noqa: E402
from modules.auth.backend.service import ensure_first_admin  # noqa: E402
from modules.finance.backend.router import router as finance_router  # noqa: E402
from modules.notifications.backend.router import router as notifications_router  # noqa: E402
from modules.masterdata.backend.router import router as masterdata_router  # noqa: E402
from modules.orders.backend.router import router as orders_router  # noqa: E402
<<<<<<< HEAD
from modules.portal.backend.router import router as portal_router  # noqa: E402
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
from modules.routing.backend.router import router as routing_router  # noqa: E402
from modules.transport.backend.router import router as transport_router  # noqa: E402
from modules.warehouse.backend.router import router as warehouse_router  # noqa: E402

settings = get_settings()

<<<<<<< HEAD
# Frontend-uud: aguulah/teever (vanilla JS) ba zahialga (React build)
ERP_UI = ROOT / "erp_frontend" / "erp_frontend"
ORDERS_DIST = ROOT / "modules" / "orders" / "frontend" / "dist"

=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4

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
<<<<<<< HEAD
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# UI file-uud: brauzer kesh-ees huuchin JS/HTML avahgui, uurchlugdsun eseh-iig ETag-aar shalgana.
UI_PATHS = ("/erp-ui", "/erp_frontend/", "/login", "/register", "/orders")


@app.middleware("http")
async def no_cache_ui(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(UI_PATHS):
        response.headers["Cache-Control"] = "no-cache"
    return response

=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4

# Modul burt router uuriin prefix-tei (/api/<modul>) tul end prefix nemehgui.
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
for r in (masterdata_router, orders_router, warehouse_router, transport_router,
<<<<<<< HEAD
          routing_router, finance_router, notifications_router, portal_router):
    app.include_router(r)


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/login")
=======
          routing_router, finance_router, notifications_router):
    app.include_router(r)


@app.get("/")
def home():
    return {"message": "Logistics ERP API is running", "status": "ok"}
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4


@app.get("/health")
def health_check():
    return {"status": "healthy"}
<<<<<<< HEAD


# ---------------- Frontend
# Modul burt tusdaa nevtreh huudas: /login (modul songoh), /login/<modul>. Neg HTML, JS n path-aas unshina.
@app.get("/login", include_in_schema=False)
@app.get("/register", include_in_schema=False)
@app.get("/login/{module}", include_in_schema=False)
def login_page(module: str | None = None):
    if module is not None and module not in MODULE_PERMISSIONS and module != "admin":
        return RedirectResponse("/login")
    return FileResponse(ERP_UI / "views" / "login.html")


@app.get("/erp-ui", include_in_schema=False)
def erp_ui():
    return FileResponse(ERP_UI / "views" / "index.html")


app.mount("/erp_frontend/static", StaticFiles(directory=ERP_UI / "static"), name="erp-static")

if ORDERS_DIST.is_dir():  # `npm run build` hiisen bol /orders/ deer
    app.mount("/orders", StaticFiles(directory=ORDERS_DIST, html=True), name="orders-ui")
else:
    @app.get("/orders", include_in_schema=False)
    @app.get("/orders/", include_in_schema=False)
    def orders_not_built():
        return {"message": "Orders UI build hiigdeegui: cd modules/orders/frontend && "
                           "npm install && npm run build  (esvel `npm run dev` -> :5174)"}
=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4
