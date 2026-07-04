import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any

from core.config import get_settings
from core.auth import require_auth
from core.validation import validate_user_id
from memory.memory_layer import MemoryLayer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryAddRequest(BaseModel):
    user_id: str
    content: str
    agent_id: str
    metadata: Optional[Dict[str, Any]] = {}

    @field_validator("user_id")
    @classmethod
    def check_user_id(cls, v: str) -> str:
        return validate_user_id(v)


class MemoryAddResponse(BaseModel):
    doc_id: Optional[str]


class MemorySearchRequest(BaseModel):
    user_id: str
    query: str
    n_results: Optional[int] = 5

    @field_validator("user_id")
    @classmethod
    def check_user_id(cls, v: str) -> str:
        return validate_user_id(v)


class MemorySearchResponse(BaseModel):
    results: List[Dict[str, Any]]


@router.post("/add", response_model=MemoryAddResponse)
async def add_memory(request: MemoryAddRequest) -> MemoryAddResponse:
async def add_memory(
    request: MemoryAddRequest,
    token_payload: dict = Depends(require_auth),
):
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Failed to add memory for user=%s agent=%s",
            request.user_id, request.agent_id,
        )
        raise HTTPException(
            status_code=500, detail="Failed to write memory"
        ) from exc

    return MemoryAddResponse(doc_id=doc_id)


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(request: MemorySearchRequest) -> MemorySearchResponse:
        return MemoryAddResponse(doc_id=doc_id)
    except Exception:
        logger.exception("add_memory failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    request: MemorySearchRequest,
    token_payload: dict = Depends(require_auth),
):
    """Search memory entries."""
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)
        memory_data = await memory_layer.read(
            user_id=request.user_id,
            query=request.query,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to search memory for user=%s", request.user_id)
        raise HTTPException(
            status_code=500, detail="Failed to search memory"
        ) from exc

    results: List[Dict[str, Any]] = []
    results.extend(memory_data.get("semantic", []))
    results.extend(memory_data.get("graph", []))

    return MemorySearchResponse(results=results[: request.n_results or 5])


@router.get("/stats/{user_id}")
async def get_memory_stats(user_id: str) -> Dict[str, Any]:
        results = []
        results.extend(memory_data.get("semantic", []))
        results.extend(memory_data.get("graph", []))

        return MemorySearchResponse(results=results[: request.n_results or 5])
    except Exception:
        logger.exception("search_memory failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/{user_id}")
async def get_memory_stats(
    user_id: str,
    token_payload: dict = Depends(require_auth),
):
    """Get memory statistics for a user."""
    validate_user_id(user_id)
    try:
        settings = get_settings()
        memory_layer = MemoryLayer(settings)
        memory_data = await memory_layer.read(user_id=user_id, query="")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get memory stats for user=%s", user_id)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve memory statistics"
        ) from exc

    semantic = memory_data.get("semantic", [])
    graph = memory_data.get("graph", [])
    return {
        "user_id": user_id,
        "vector_store_entries": len(semantic),
        "graph_memory_entries": len(graph),
        "total_entries": len(semantic) + len(graph),
    }


@router.delete("/{user_id}")
async def clear_user_memory(user_id: str) -> Dict[str, str]:
    """Clear all memory for a user."""
    return {
        "message": f"Memory clear not fully implemented for user {user_id}",
        "user_id": user_id,
    }

        memory_data = await memory_layer.read(user_id=user_id, query="")

        return {
            "user_id": user_id,
            "vector_store_entries": len(memory_data.get("semantic", [])),
            "graph_memory_entries": len(memory_data.get("graph", [])),
            "total_entries": len(memory_data.get("semantic", [])) + len(memory_data.get("graph", [])),
        }
    except Exception:
        logger.exception("get_memory_stats failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}")
async def clear_user_memory(
    user_id: str,
    token_payload: dict = Depends(require_auth),
):
    """Clear all memory for a user."""
    validate_user_id(user_id)
    try:
        return {
            "message": f"Memory clear not fully implemented for user {user_id}",
            "user_id": user_id,
        }
    except Exception:
        logger.exception("clear_user_memory failed")
        raise HTTPException(status_code=500, detail="Internal server error")
