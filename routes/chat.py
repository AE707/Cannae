from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from agents import get_agent, AGENT_REGISTRY, AGENT_DESCRIPTIONS
from core.config import get_settings
from memory.memory_layer import MemoryLayer


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = []
    agent_type: str = "ceo"  # "ceo", "coach", "seo", or "cfo"


class ChatResponse(BaseModel):
    response: str
    agent_used: str


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle general chat requests with specific agent selection."""
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)

        agent = get_agent(request.agent_type.lower(), memory_layer, settings)

        response = await agent.invoke(
            request.user_id,
            request.message,
            request.history or [],
        )

        return ChatResponse(
            response=response,
            agent_used=request.agent_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """List available agents."""
    return {
        "agents": list(AGENT_REGISTRY.keys()),
        "descriptions": AGENT_DESCRIPTIONS,
    }
