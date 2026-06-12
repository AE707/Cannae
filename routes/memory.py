from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from core.config import get_settings
from memory.memory_layer import MemoryLayer


router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryAddRequest(BaseModel):
    user_id: str
    content: str
    agent_id: str
    metadata: Optional[Dict[str, Any]] = {}


class MemoryAddResponse(BaseModel):
    doc_id: str


class MemorySearchRequest(BaseModel):
    user_id: str
    query: str
    n_results: Optional[int] = 5


class MemorySearchResponse(BaseModel):
    results: List[Dict[str, Any]]


@router.post("/add", response_model=MemoryAddResponse)
async def add_memory(request: MemoryAddRequest):
    """Add a memory entry."""
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)
        doc_id = await memory_layer.write(
            user_id=request.user_id,
            content=request.content,
            agent_id=request.agent_id,
            metadata=request.metadata or {},
        )

        return MemoryAddResponse(doc_id=doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(request: MemorySearchRequest):
    """Search memory entries."""
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)
        memory_data = await memory_layer.read(
            user_id=request.user_id,
            query=request.query,
        )

        # Combine semantic and graph results for simplicity
        results = []
        results.extend(memory_data.get("semantic", []))
        results.extend(memory_data.get("graph", []))

        return MemorySearchResponse(results=results[: request.n_results or 5])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """Get memory statistics for a user."""
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)

        # Get memory data to calculate stats
        memory_data = await memory_layer.read(user_id=user_id, query="")

        return {
            "user_id": user_id,
            "vector_store_entries": len(memory_data.get("semantic", [])),
            "graph_memory_entries": len(memory_data.get("graph", [])),
            "total_entries": len(memory_data.get("semantic", [])) + len(memory_data.get("graph", [])),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def clear_user_memory(user_id: str):
    """Clear all memory for a user."""
    try:
        # Note: This would require implementing clear methods in memory layers
        # For now, we'll return a placeholder response

        return {
            "message": f"Memory clear not fully implemented for user {user_id}",
            "user_id": user_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))