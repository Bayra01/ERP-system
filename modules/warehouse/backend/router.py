from fastapi import APIRouter

router = APIRouter(prefix="/api/warehouse", tags=["warehouse"])


@router.get("/health")
def health():
    return {"module": "warehouse", "status": "ok"}
