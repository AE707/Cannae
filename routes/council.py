from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from agents.council import Council
from core.config import get_settings
from memory.memory_layer import MemoryLayer


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
async def council_chat(request: ChatRequest):
    """Handle council chat requests with agent routing and handoff."""
    try:
        council = Council()
        response = await council.invoke(
            request.user_id,
            request.message,
            request.history or [],
        )

        # Determine which agent was primarily used (simplified)
        # In a full implementation, we'd track this from the council state
        agent_used = "council"  # Placeholder

        return ChatResponse(
            response=response,
            agent_used=agent_used,
            handoff_occurred=False,  # Placeholder
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(user_id: str, query: str = ""):
    """Retrieve memory for a user."""
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)
        memory_data = await memory_layer.read(user_id, query or "")

        return MemoryResponse(
            semantic=memory_data.get("semantic", []),
            graph=memory_data.get("graph", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{user_id}")
async def clear_memory(user_id: str):
    """Clear memory for a user (for testing purposes)."""
    try:
        # Note: This would require implementing a clear method in memory_layer
        # For now, we'll return a placeholder response
        return {"message": f"Memory clear not fully implemented for user {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))