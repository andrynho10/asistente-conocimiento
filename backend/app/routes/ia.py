"""
IA (Inteligencia Artificial) Routes

FastAPI router for AI/LLM related endpoints.
Provides health check and generation capabilities with proper
error handling, logging, and rate limiting.
"""

import time
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.services.llm_service import get_llm_service, OllamaLLMService
from app.services.retrieval_service import RetrievalService
from app.database import get_session
from app.schemas.ia import (
    HealthResponse,
    GenerationRequest,
    GenerationResponse,
    ModelListResponse,
    ModelInfo,
    RetrieveRequest,
    RetrieveResponse,
    ErrorResponse
)

# Import admin dependency for endpoint protection
try:
    from app.middleware.auth import get_current_user, require_role

    def get_current_admin_user(current_user = Depends(get_current_user)):
        """Require admin role for endpoint access."""
        return require_role("admin")(current_user)
except ImportError:
    # Fallback if auth module not available
    async def get_current_admin_user():
        """Placeholder admin dependency - should be replaced with actual auth."""
        raise HTTPException(
            status_code=501,
            detail="Authentication module not available"
        )

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/ia",
    tags=["Inteligencia Artificial"],
    responses={404: {"description": "Not found"}},
)

# Rate limiting storage (simple in-memory for demo)
rate_limits: Dict[str, Dict[str, Any]] = {}


def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key from request."""
    # Use client IP as key (could be enhanced with user ID in future)
    return f"rate_limit:{request.client.host}"


def check_rate_limit(request: Request, limit: int = 10, window: int = 60) -> bool:
    """
    Simple rate limiting check.

    Args:
        request: FastAPI request object
        limit: Number of requests allowed
        window: Time window in seconds

    Returns:
        True if request is allowed, False otherwise
    """
    key = get_rate_limit_key(request)
    now = time.time()

    if key not in rate_limits:
        rate_limits[key] = {"count": 0, "window_start": now}

    # Reset window if expired
    if now - rate_limits[key]["window_start"] > window:
        rate_limits[key] = {"count": 0, "window_start": now}

    # Check limit
    if rate_limits[key]["count"] >= limit:
        return False

    # Increment counter
    rate_limits[key]["count"] += 1
    return True


async def get_llm_service() -> OllamaLLMService:
    """Dependency injection for LLM service."""
    return get_llm_service()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="IA Service Health Check",
    description="Check if the Ollama AI service is available and responsive",
    responses={
        200: {
            "description": "Service is healthy and available",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "model": "llama3.1:8b-instruct-q4_K_M",
                        "ollama_version": "0.1.20",
                        "available_at": "2025-11-13T10:30:00Z",
                        "response_time_ms": 125.5
                    }
                }
            }
        },
        503: {
            "description": "Service is unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unavailable",
                        "error": "Connection refused",
                        "available_at": "2025-11-13T10:30:00Z",
                        "response_time_ms": 1000.0
                    }
                }
            }
        }
    }
)
async def health_check(
    request: Request,
    llm_svc: OllamaLLMService = Depends(get_llm_service)
):
    """
    Check IA service health and availability.

    This endpoint verifies that the Ollama service is running and
    the configured model is available. It returns detailed information
    about the service status including response times.
    """
    from datetime import datetime

    # Check rate limiting
    if not check_rate_limit(request, limit=20, window=60):
        raise HTTPException(
            status_code=429,
            detail="Too many requests - rate limit exceeded"
        )

    start_time = time.time()
    now = datetime.utcnow()

    try:
        # Perform health check
        is_healthy = await llm_svc.health_check_async()
        response_time_ms = (time.time() - start_time) * 1000

        if is_healthy:
            # Get additional info
            ollama_version = await llm_svc.get_ollama_version()
            model_info = llm_svc.get_model_info()

            response = HealthResponse(
                status="ok",
                model=llm_svc.model,
                ollama_version=ollama_version,
                available_at=now,
                response_time_ms=response_time_ms
            )

            logger.info(
                f"IA health check successful - model: {llm_svc.model}, "
                f"version: {ollama_version}, response_time: {response_time_ms:.2f}ms"
            )

            return response

        else:
            # Service is not responding
            response = HealthResponse(
                status="unavailable",
                error="Ollama service not responding",
                available_at=now,
                response_time_ms=response_time_ms
            )

            logger.warning(
                f"IA health check failed - service unavailable, "
                f"response_time: {response_time_ms:.2f}ms"
            )

            return JSONResponse(
                status_code=503,
                content=response.dict()
            )

    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000

        error_msg = f"Health check error: {str(e)}"
        logger.error(error_msg)

        response = HealthResponse(
            status="unavailable",
            error=error_msg,
            available_at=now,
            response_time_ms=response_time_ms
        )

        return JSONResponse(
            status_code=503,
            content=response.dict()
        )


@router.post(
    "/generate",
    response_model=GenerationResponse,
    summary="Generate Text with AI",
    description="Generate text using the configured LLM model",
    responses={
        200: {
            "description": "Text generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "response": "El aprendizaje automático es una rama de la inteligencia artificial...",
                        "model": "llama3.1:8b-instruct-q4_K_M",
                        "prompt_tokens": 8,
                        "response_tokens": 35,
                        "total_tokens": 43,
                        "generation_time_ms": 1250.0,
                        "temperature": 0.3
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        503: {"description": "AI service unavailable"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def generate_text(
    request: Request,
    generation_request: GenerationRequest,
    llm_svc: OllamaLLMService = Depends(get_llm_service)
):
    """
    Generate text using the local LLM model.

    This endpoint takes a prompt and generates text using the configured
    LLM model (Llama 3.1). It includes rate limiting and proper error handling.
    """
    # Check rate limiting (more restrictive for generation)
    if not check_rate_limit(request, limit=5, window=60):
        raise HTTPException(
            status_code=429,
            detail="Too many generation requests - rate limit exceeded"
        )

    start_time = time.time()

    try:
        # Check if service is healthy first
        if not await llm_svc.health_check_async():
            raise HTTPException(
                status_code=503,
                detail="AI service is currently unavailable"
            )

        # Generate response
        logger.info(f"Generating text for prompt: {generation_request.prompt[:100]}...")

        generated_text = await llm_svc.generate_response_async(
            prompt=generation_request.prompt,
            temperature=generation_request.temperature,
            max_tokens=generation_request.max_tokens
        )

        generation_time_ms = (time.time() - start_time) * 1000

        response = GenerationResponse(
            response=generated_text,
            model=llm_svc.model,
            temperature=generation_request.temperature,
            generation_time_ms=generation_time_ms
            # Note: token counts would require additional Ollama API features
        )

        logger.info(
            f"Text generation completed - model: {llm_svc.model}, "
            f"response_length: {len(generated_text)}, "
            f"generation_time: {generation_time_ms:.2f}ms"
        )

        return response

    except ValueError as e:
        logger.warning(f"Invalid generation request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        generation_time_ms = (time.time() - start_time) * 1000

        error_msg = f"Generation failed: {str(e)}"
        logger.error(error_msg)

        raise HTTPException(
            status_code=500,
            detail=f"Text generation failed: {str(e)}"
        )


@router.get(
    "/models",
    response_model=ModelListResponse,
    summary="List Available Models",
    description="Get list of all available LLM models",
    responses={
        200: {
            "description": "List of available models",
            "content": {
                "application/json": {
                    "example": {
                        "models": [
                            {
                                "name": "llama3.1:8b-instruct-q4_K_M",
                                "size": 5033164800,
                                "digest": "sha256:abc123...",
                                "modified_at": "2025-11-13T10:30:00Z"
                            }
                        ],
                        "total": 1
                    }
                }
            }
        },
        503: {"description": "AI service unavailable"}
    }
)
async def list_models(
    request: Request,
    llm_svc: OllamaLLMService = Depends(get_llm_service)
):
    """
    Get list of available LLM models.

    Returns information about all models that are available
    in the Ollama service.
    """
    # Check rate limiting
    if not check_rate_limit(request, limit=10, window=60):
        raise HTTPException(
            status_code=429,
            detail="Too many requests - rate limit exceeded"
        )

    try:
        # Check if service is healthy
        if not await llm_svc.health_check_async():
            raise HTTPException(
                status_code=503,
                detail="AI service is currently unavailable"
            )

        # Get models list
        models_data = llm_svc.client.list()
        models = models_data.get('models', [])

        model_infos = []
        for model in models:
            model_info = ModelInfo(
                name=model.get('name', ''),
                size=model.get('size'),
                digest=model.get('digest'),
                modified_at=model.get('modified_at'),
                details=model
            )
            model_infos.append(model_info)

        response = ModelListResponse(
            models=model_infos,
            total=len(model_infos)
        )

        logger.info(f"Retrieved {len(model_infos)} available models")

        return response

    except Exception as e:
        error_msg = f"Failed to list models: {str(e)}"
        logger.error(error_msg)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve models: {str(e)}"
        )


@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
    summary="Retrieve Relevant Documents",
    description="Retrieve relevant documents for AI queries using advanced search and ranking",
    responses={
        200: {
            "description": "Documents retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "query": "políticas de vacaciones",
                        "optimized_query": "política OR regla OR directriz OR vacaciones OR descanso OR licencia",
                        "total_documents": 3,
                        "documents": [
                            {
                                "document_id": 1,
                                "title": "Política de Vacaciones Anuales",
                                "category": "RRHH",
                                "relevance_score": 0.95,
                                "snippet": "Los empleados tienen derecho a 15 días hábiles de <mark>vacaciones</mark> anuales...",
                                "upload_date": "2025-11-13T10:30:00Z"
                            }
                        ],
                        "processing_time_ms": 45.2
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        403: {"description": "Admin access required"},
        500: {"description": "Retrieval service error"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def retrieve_documents(
    request: Request,
    retrieve_request: RetrieveRequest,
    db=Depends(get_session),
    current_user=Depends(get_current_admin_user)  # Admin only endpoint
):
    """
    Retrieve relevant documents for AI context generation.

    This endpoint uses advanced retrieval techniques including:
    - Query optimization with synonym expansion
    - Text normalization and stopword filtering
    - BM25 ranking with relevance scores
    - Smart filtering for low-relevance results

    **Admin Only**: This endpoint is restricted to admin users for debugging
    and testing purposes. Production RAG usage should be integrated directly
    in the AI generation pipeline.
    """
    # Check rate limiting
    if not check_rate_limit(request, limit=15, window=60):
        raise HTTPException(
            status_code=429,
            detail="Too many retrieval requests - rate limit exceeded"
        )

    start_time = time.time()

    try:
        logger.info(f"Retrieving documents for query: {retrieve_request.query}")

        # Perform retrieval
        documents = await RetrievalService.retrieve_relevant_documents(
            query=retrieve_request.query,
            top_k=retrieve_request.top_k,
            db=db
        )

        processing_time_ms = (time.time() - start_time) * 1000

        # Convert documents to dict format for response
        documents_dict = []
        for doc in documents:
            documents_dict.append({
                "document_id": doc.document_id,
                "title": doc.title,
                "category": doc.category,
                "relevance_score": doc.relevance_score,
                "snippet": doc.snippet,
                "upload_date": doc.upload_date.isoformat() if doc.upload_date else None
            })

        # Get optimized query for debugging
        optimized_query = RetrievalService._optimize_query(retrieve_request.query)

        response = RetrieveResponse(
            query=retrieve_request.query,
            optimized_query=optimized_query,
            total_documents=len(documents),
            documents=documents_dict,
            processing_time_ms=processing_time_ms
        )

        logger.info(
            f"Document retrieval completed - query: {retrieve_request.query}, "
            f"documents: {len(documents)}, processing_time: {processing_time_ms:.2f}ms"
        )

        return response

    except ValueError as e:
        logger.warning(f"Invalid retrieval request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000

        error_msg = f"Document retrieval failed: {str(e)}"
        logger.error(error_msg)

        raise HTTPException(
            status_code=500,
            detail=f"Document retrieval failed: {str(e)}"
        )