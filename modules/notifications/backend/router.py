from fastapi import APIRouter

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/health")
def health():
    return {"module": "notifications", "status": "ok"}
