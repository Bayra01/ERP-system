from fastapi import APIRouter

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/health")
def health():
    return {"module": "orders", "status": "ok"}
