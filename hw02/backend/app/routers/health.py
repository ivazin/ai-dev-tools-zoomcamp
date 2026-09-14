from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("/live")
async def health_live():
    return {"status": "ok"}


@router.get("/ready")
async def health_ready():
    return {"status": "ready"}
