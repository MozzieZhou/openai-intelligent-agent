from fastapi import APIRouter
from pydantic import BaseModel

from app.bootstrap.container import build_agent_orchestrator

router = APIRouter()
orchestrator = build_agent_orchestrator()


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    query: str


@router.post("/chat")
async def chat(request: ChatRequest) -> dict:
    return await orchestrator.handle(request.query)
