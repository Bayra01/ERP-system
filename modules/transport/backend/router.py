from fastapi import APIRouter

router = APIRouter(prefix="/api/transport", tags=["transport"])


@router.get("/health")
def health():
    return {"module": "transport", "status": "ok"}
