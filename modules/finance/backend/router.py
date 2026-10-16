from fastapi import APIRouter

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/health")
def health():
    return {"module": "finance", "status": "ok"}
