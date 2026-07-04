import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any

from agents.council import Council
from core.config import get_settings
from core.auth import require_auth
from core.validation import validate_user_id
from memory.memory_layer import MemoryLayer
from services.llm import LLMServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/council", tags=["council"])


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = []

    @field_validator("user_id")
    @classmethod
    def check_user_id(cls, v: str) -> str:
        return validate_user_id(v)


class ChatResponse(BaseModel):
    response: str
    agent_used: str
    handoff_occurred: bool


class MemoryResponse(BaseModel):
    semantic: List[Dict[str, Any]]
    graph: List[Dict[str, Any]]


@router.post("/chat", response_model=ChatResponse)
async def council_chat(request: ChatRequest) -> ChatResponse:
async def council_chat(
    request: ChatRequest,
    token_payload: dict = Depends(require_auth),
):
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

        agent_used = "council"

        return ChatResponse(
            response=response,
            agent_used=agent_used,
            handoff_occurred=False,
        )
    except Exception:
        logger.exception("council_chat failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(
    user_id: str,
    query: str = "",
    token_payload: dict = Depends(require_auth),
):
    """Retrieve memory for a user."""
    validate_user_id(user_id)
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
        return MemoryResponse(
            semantic=memory_data.get("semantic", []),
            graph=memory_data.get("graph", []),
        )
    except Exception:
        logger.exception("get_memory failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/memory/{user_id}")
async def clear_memory(
    user_id: str,
    token_payload: dict = Depends(require_auth),
):
    """Clear memory for a user (for testing purposes)."""
    validate_user_id(user_id)
    try:
        return {"message": f"Memory clear not fully implemented for user {user_id}"}
    except Exception:
        logger.exception("clear_memory failed")
        raise HTTPException(status_code=500, detail="Internal server error")
