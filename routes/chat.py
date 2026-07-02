import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any

from agents.ceo_agent import CEOAgent
from agents.coach_agent import CoachAgent
from agents.seo_agent import SEOSAgent
from agents.cfo_agent import CFOAgent
from core.config import get_settings
from core.auth import require_auth
from core.validation import validate_user_id
from memory.memory_layer import MemoryLayer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = []
    agent_type: str = "ceo"  # "ceo", "coach", "seo", or "cfo"

    @field_validator("user_id")
    @classmethod
    def check_user_id(cls, v: str) -> str:
        return validate_user_id(v)


class ChatResponse(BaseModel):
    response: str
    agent_used: str


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    token_payload: dict = Depends(require_auth),
):
    """Handle general chat requests with specific agent selection."""
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)

        if request.agent_type.lower() == "ceo":
            agent = CEOAgent(memory_layer, settings)
        elif request.agent_type.lower() == "coach":
            agent = CoachAgent(memory_layer, settings)
        elif request.agent_type.lower() == "seo":
            agent = SEOSAgent(memory_layer, settings)
        elif request.agent_type.lower() == "cfo":
            agent = CFOAgent(memory_layer, settings)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent_type: {request.agent_type}. Must be 'ceo', 'coach', 'seo', or 'cfo'",
            )

        response = await agent.invoke(
            request.user_id,
            request.message,
            request.history or [],
        )

        return ChatResponse(
            response=response,
            agent_used=request.agent_type,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("chat_endpoint failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/agents")
async def list_agents():
    """List available agents (public endpoint)."""
    return {
        "agents": ["ceo", "coach", "seo", "cfo"],
        "descriptions": {
            "ceo": "Strategic advisor focused on high-leverage decisions",
            "coach": "Accountability partner focused on goal tracking and follow-through",
            "seo": "Search engine optimization and content strategy specialist",
            "cfo": "Financial analysis and strategic finance specialist",
        },
    }
