import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from agents.council import Council
from core.config import get_settings
from memory.memory_layer import MemoryLayer
from services.llm import LLMServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/council", tags=["council"])


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = []


class ChatResponse(BaseModel):
    response: str
    agent_used: str
    handoff_occurred: bool


class MemoryResponse(BaseModel):
    semantic: List[Dict[str, Any]]
    graph: List[Dict[str, Any]]


@router.post("/chat", response_model=ChatResponse)
async def council_chat(request: ChatRequest) -> ChatResponse:
    """Handle council chat requests with agent routing and handoff."""
    try:
        council = Council()
        response = await council.invoke(
            request.user_id,
            request.message,
            request.history or [],
        )
    except LLMServiceError as exc:
        logger.error("LLM service error in council chat: %s", exc)
        status = 503 if exc.retryable else 502
        raise HTTPException(status_code=status, detail="AI service temporarily unavailable") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in council chat")
        raise HTTPException(
            status_code=500, detail="Internal server error"
        ) from exc

    return ChatResponse(
        response=response,
        agent_used="council",
        handoff_occurred=False,
    )


@router.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(user_id: str, query: str = "") -> MemoryResponse:
    """Retrieve memory for a user."""
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)
        memory_data = await memory_layer.read(user_id, query or "")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error retrieving memory for user=%s", user_id)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve memory"
        ) from exc

    return MemoryResponse(
        semantic=memory_data.get("semantic", []),
        graph=memory_data.get("graph", []),
    )


@router.delete("/memory/{user_id}")
async def clear_memory(user_id: str) -> Dict[str, str]:
    """Clear memory for a user (for testing purposes)."""
    return {"message": f"Memory clear not fully implemented for user {user_id}"}