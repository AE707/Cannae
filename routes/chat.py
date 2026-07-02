import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from agents.ceo_agent import CEOAgent
from agents.coach_agent import CoachAgent
from agents.seo_agent import SEOSAgent
from agents.cfo_agent import CFOAgent
from core.config import get_settings
from memory.memory_layer import MemoryLayer
from services.llm import LLMServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

VALID_AGENT_TYPES = ("ceo", "coach", "seo", "cfo")


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = []
    agent_type: str = "ceo"


class ChatResponse(BaseModel):
    response: str
    agent_used: str


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Handle general chat requests with specific agent selection."""
    agent_type = request.agent_type.lower()
    if agent_type not in VALID_AGENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent_type: {request.agent_type}. Must be one of {VALID_AGENT_TYPES}",
        )

    settings = get_settings()
    memory_layer = MemoryLayer(settings)

    agents = {
        "ceo": CEOAgent,
        "coach": CoachAgent,
        "seo": SEOSAgent,
        "cfo": CFOAgent,
    }
    agent = agents[agent_type](memory_layer, settings)

    try:
        response = await agent.invoke(
            request.user_id,
            request.message,
            request.history or [],
        )
    except LLMServiceError as exc:
        logger.error("LLM service error in chat (agent=%s): %s", agent_type, exc)
        status = 503 if exc.retryable else 502
        raise HTTPException(
            status_code=status, detail="AI service temporarily unavailable"
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in chat endpoint (agent=%s)", agent_type)
        raise HTTPException(
            status_code=500, detail="Internal server error"
        ) from exc

    return ChatResponse(
        response=response,
        agent_used=agent_type,
    )


@router.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """List available agents."""
    return {
        "agents": list(VALID_AGENT_TYPES),
        "descriptions": {
            "ceo": "Strategic advisor focused on high-leverage decisions",
            "coach": "Accountability partner focused on goal tracking and follow-through",
            "seo": "Search engine optimization and content strategy specialist",
            "cfo": "Financial analysis and strategic finance specialist",
        },
    }