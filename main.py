
from fastapi import FastAPI  # pyright: ignore[reportMissingImports]
from pathlib import Path
import sys

app = FastAPI(
    title="Logistics ERP API",
    description="Logistics ERP system backend",
    version="1.0.0",
)

# Import module routers
# Make imports work when the app is launched outside the project directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from modules.orders.backend.router import router as orders_router  # pyright: ignore[reportMissingImports]
from modules.warehouse.backend.router import router as warehouse_router  # pyright: ignore[reportMissingImports]
from modules.transport.backend.router import router as transport_router  # pyright: ignore[reportMissingImports]
from modules.routing.backend.router import router as routing_router
from modules.finance.backend.router import router as finance_router  # pyright: ignore[reportMissingImports]
from modules.notifications.backend.router import router as notifications_router  # pyright: ignore[reportMissingImports]

# Register routers
app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
app.include_router(warehouse_router, prefix="/api/warehouse", tags=["Warehouse"])
app.include_router(transport_router, prefix="/api/transport", tags=["Transport"])
app.include_router(routing_router, prefix="/api/routing", tags=["Routing"])
app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])


@app.get("/")
def home():
    return {
        "message": "Logistics ERP API is running",
        "status": "ok",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
