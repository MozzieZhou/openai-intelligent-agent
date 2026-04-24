from fastapi import APIRouter

router = APIRouter()


@router.get("/approvals/health")
async def approval_health() -> dict:
    return {"status": "ok"}
