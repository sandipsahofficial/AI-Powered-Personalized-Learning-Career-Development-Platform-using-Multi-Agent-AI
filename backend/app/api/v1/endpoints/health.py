import time
import logging
from typing import Dict, Any
import httpx
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.db.session import check_database_connection
from app.db.redis import redis_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", summary="Overall Application Health")
async def get_overall_health():
    """
    Checks the status of the FastAPI backend and provides summary of subsystem health.
    """
    db_status = await check_database_connection()
    redis_status = await redis_manager.check_connection()
    
    # Fast non-blocking check on LLM
    llm_reachable = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            llm_reachable = resp.status_code == 200
    except Exception:
        llm_reachable = False

    is_healthy = db_status.get("status") == "healthy" and redis_status.get("status") == "healthy"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
        "services": {
            "database": db_status.get("status"),
            "redis": redis_status.get("status"),
            "llm": "healthy" if llm_reachable else "unreachable"
        }
    }


@router.get("/database", summary="PostgreSQL and pgvector Health")
async def get_database_health():
    """
    Directly tests PostgreSQL connection pooling and pgvector extension readiness.
    """
    result = await check_database_connection()
    status_code = status.HTTP_200_OK if result.get("status") == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=result)


@router.get("/redis", summary="Redis Connectivity and Cache Health")
async def get_redis_health():
    """
    Directly tests Redis connectivity, ping latency, and read/write capability.
    """
    result = await redis_manager.check_connection()
    status_code = status.HTTP_200_OK if result.get("status") == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=result)


@router.get("/llm", summary="Ollama Local LLM Health and Model Inspection")
async def get_llm_health():
    """
    Inspects connectivity to the Ollama endpoint, queries available local models, and measures latency.
    """
    start_time = time.perf_counter()
    endpoint = f"{settings.OLLAMA_BASE_URL}/api/tags"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(endpoint)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name") for m in models]
                
                # Check for configured instruction and reasoning models
                configured_present = {
                    "instruction_model": settings.LLM_INSTRUCTION_MODEL in model_names,
                    "reasoning_model": settings.LLM_REASONING_MODEL in model_names
                }

                return {
                    "status": "healthy",
                    "ollama_base_url": settings.OLLAMA_BASE_URL,
                    "latency_ms": latency_ms,
                    "total_models": len(models),
                    "installed_models": model_names,
                    "configured_models": {
                        "instruction": settings.LLM_INSTRUCTION_MODEL,
                        "reasoning": settings.LLM_REASONING_MODEL,
                        "embedding": settings.LLM_EMBEDDING_MODEL
                    },
                    "configured_models_available": configured_present
                }
            else:
                return JSONResponse(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    content={
                        "status": "unhealthy",
                        "ollama_base_url": settings.OLLAMA_BASE_URL,
                        "error": f"Ollama returned HTTP status {response.status_code}",
                        "latency_ms": latency_ms
                    }
                )
    except httpx.ConnectError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unreachable",
                "ollama_base_url": settings.OLLAMA_BASE_URL,
                "error": "Failed to establish TCP connection to Ollama. Ensure Ollama is running.",
                "hint": "Run 'ollama serve' on the host or start the ollama docker container."
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "ollama_base_url": settings.OLLAMA_BASE_URL,
                "error": str(e)
            }
        )
