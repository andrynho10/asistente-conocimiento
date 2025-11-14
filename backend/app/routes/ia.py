"""
IA (Inteligencia Artificial) Routes

FastAPI router for AI/LLM related endpoints.
Provides health check and generation capabilities with proper
error handling, logging, and rate limiting.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.services.llm_service import get_llm_service, OllamaLLMService
from app.services.retrieval_service import RetrievalService
from app.services.learning_path_service import LearningPathService
from app.database import get_session
from app.models import LearningPath
from sqlmodel import select
from app.schemas.ia import (
    HealthResponse,
    GenerationRequest,
    GenerationResponse,
    ModelListResponse,
    ModelInfo,
    RetrieveRequest,
    RetrieveResponse,
    QueryRequest,
    QueryResponse,
    MetricsResponse,
    ErrorResponse,
    SummaryGenerationRequest,
    SummaryGenerationResponse,
    QuizGenerationRequest,
    QuizGenerationResponse,
    QuizSubmissionRequest,
    QuizSubmissionResponse,
    LearningPathGenerationRequest,
    LearningPathGenerationResponse
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


def get_llm_service_dependency() -> OllamaLLMService:
    """Dependency injection for LLM service."""
    return OllamaLLMService()


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
    llm_svc: OllamaLLMService = Depends(get_llm_service_dependency)
):
    """
    Check IA service health and availability.

    This endpoint verifies that the Ollama service is running and
    the configured model is available. It returns detailed information
    about the service status including response times and cache statistics.

    Task 10 Addition:
    - Extends response to include cache_stats (cache_size, hit_rate, memory_usage_mb)
    - Provides visibility into caching layer performance (AC#2)
    """
    from datetime import datetime

    # Check rate limiting
    if not check_rate_limit(request, limit=20, window=60):
        raise HTTPException(
            status_code=429,
            detail="Too many requests - rate limit exceeded"
        )

    start_time = time.time()
    now = datetime.now(timezone.utc)

    try:
        # Perform health check
        is_healthy = await llm_svc.health_check_async()
        response_time_ms = (time.time() - start_time) * 1000

        if is_healthy:
            # Get additional info
            ollama_version = await llm_svc.get_ollama_version()
            model_info = llm_svc.get_model_info()

            # Task 10: Get cache statistics from CacheService (AC#2)
            from app.services.rag_service import response_cache, retrieval_cache

            response_cache_stats = response_cache.get_stats()
            retrieval_cache_stats = retrieval_cache.get_stats()

            # Combine statistics from both caches
            total_cache_size = response_cache_stats.get("size", 0) + retrieval_cache_stats.get("size", 0)
            total_hits = response_cache_stats.get("hits", 0) + retrieval_cache_stats.get("hits", 0)
            total_misses = response_cache_stats.get("misses", 0) + retrieval_cache_stats.get("misses", 0)

            # Calculate overall hit rate
            total_requests = total_hits + total_misses
            cache_hit_rate = (total_hits / total_requests) if total_requests > 0 else 0.0

            # Estimate memory usage (approximate: 1KB per entry average)
            memory_usage_mb = round((total_cache_size * 1.0) / 1024, 2)

            # Build cache_stats object
            cache_stats = {
                "cache_size": total_cache_size,
                "hit_rate": round(cache_hit_rate, 4),
                "memory_usage_mb": memory_usage_mb,
                "response_cache_size": response_cache_stats.get("size", 0),
                "retrieval_cache_size": retrieval_cache_stats.get("size", 0)
            }

            response = HealthResponse(
                status="ok",
                model=llm_svc.model,
                ollama_version=ollama_version,
                available_at=now,
                response_time_ms=response_time_ms,
                cache_stats=cache_stats  # Task 10: Include cache statistics
            )

            logger.info(
                f"IA health check successful - model: {llm_svc.model}, "
                f"version: {ollama_version}, response_time: {response_time_ms:.2f}ms, "
                f"cache_hit_rate: {cache_hit_rate:.2%}, cache_size: {total_cache_size}"
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
                content=response.model_dump(mode='json')
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
            content=response.model_dump(mode='json')
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
    llm_svc: OllamaLLMService = Depends(get_llm_service_dependency)
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
    llm_svc: OllamaLLMService = Depends(get_llm_service_dependency)
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


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Conversational AI Query",
    description="Submit natural language queries and receive AI-powered responses grounded in corporate documents",
    responses={
        200: {
            "description": "Query processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "query": "¿Cuál es la política de vacaciones?",
                        "answer": "Según la política de vacaciones, los empleados tienen derecho a 15 días hábiles anuales...",
                        "sources": [
                            {
                                "document_id": 1,
                                "title": "Política de Vacaciones Anuales",
                                "relevance_score": 0.95
                            }
                        ],
                        "response_time_ms": 1245.5,
                        "documents_retrieved": 1,
                        "timestamp": "2025-11-13T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid query (length, context_mode)"},
        401: {"description": "Unauthenticated - authentication required"},
        429: {"description": "Rate limit exceeded - 10 queries per 60 seconds"},
        503: {"description": "AI service unavailable"}
    }
)
async def query_ai(
    request: Request,
    query_request: QueryRequest,
    db=Depends(get_session),
    current_user=Depends(get_current_user),
    llm_svc: OllamaLLMService = Depends(get_llm_service_dependency)
):
    """
    Submit natural language queries to the conversational AI system.

    This endpoint implements the complete RAG pipeline:
    1. Validates query format (10-500 characters, valid context_mode)
    2. Applies rate limiting (10 queries per 60 seconds per user)
    3. Executes RAG pipeline (retrieval + generation with caching)
    4. Records query and performance metrics with cache_hit tracking
    5. Returns structured response with sources and timing info

    AC#2: Query Endpoint with Response Caching
    AC#3: Retrieval Service Integration
    AC#4: RAG Pipeline Implementation via RAGService
    AC#5: Response Structure and Metadata
    AC#6: Rate Limiting Enforcement
    AC#7: Audit Logging
    AC#8: Performance Metrics Recording (Task 6)

    Task 6 Implementation:
    - Uses RAGService.rag_query() which includes cache_hit flag
    - Extracts timing metrics: retrieval_time_ms, llm_time_ms
    - Records both Query and PerformanceMetric records atomically
    """
    from app.models.query import Query, PerformanceMetric
    from app.services.rag_service import RAGService
    from sqlmodel import Session
    import json

    start_time = time.time()

    try:
        # AC#6: Rate limiting - 10 queries per 60 seconds per user
        user_rate_key = f"rate_limit:user:{current_user.id}"
        now = time.time()

        if user_rate_key not in rate_limits:
            rate_limits[user_rate_key] = {"count": 0, "window_start": now}

        # Reset window if expired (60 seconds)
        if now - rate_limits[user_rate_key]["window_start"] > 60:
            rate_limits[user_rate_key] = {"count": 0, "window_start": now}

        # Check limit
        if rate_limits[user_rate_key]["count"] >= 10:
            logger.warning(
                f"Rate limit exceeded for user {current_user.id}: "
                f"{rate_limits[user_rate_key]['count']} requests in current window"
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: 10 queries per 60 seconds per user",
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(rate_limits[user_rate_key]["window_start"] + 60))
                }
            )

        # Increment counter
        rate_limits[user_rate_key]["count"] += 1
        remaining = 10 - rate_limits[user_rate_key]["count"]
        reset_time = int(rate_limits[user_rate_key]["window_start"] + 60)

        logger.info(
            f"Query received from user {current_user.id}: "
            f"{query_request.query[:100]}... (context_mode: {query_request.context_mode})"
        )

        # Check if service is available
        if not await llm_svc.health_check_async():
            raise HTTPException(
                status_code=503,
                detail="AI service is currently unavailable"
            )

        # Execute RAG pipeline using RAGService (Task 6: integrates caching + metrics)
        rag_response = await RAGService.rag_query(
            user_query=query_request.query,
            user_id=current_user.id,
            session=db,
            llm_service=llm_svc,
            top_k=query_request.top_k or 3,
            temperature=query_request.temperature or 0.7,
            max_tokens=query_request.max_tokens or 500
        )

        # Extract timing metrics and cache_hit from RAG response
        retrieval_time_ms = rag_response.get("retrieval_time_ms", 0.0)
        llm_time_ms = rag_response.get("llm_time_ms", 0.0)
        response_time_ms = rag_response.get("response_time_ms", (time.time() - start_time) * 1000)
        cache_hit = rag_response.get("cache_hit", False)

        # Build source list from RAG response
        sources = rag_response.get("sources", [])

        # Prepare response
        response = QueryResponse(
            query=query_request.query,
            answer=rag_response["answer"],
            sources=sources,
            response_time_ms=response_time_ms,
            documents_retrieved=rag_response.get("documents_retrieved", 0)
        )

        # Task 6: Store query and metrics in database (AC#8)
        try:
            # Convert sources to JSON
            sources_json = json.dumps([
                {
                    "document_id": s.get("document_id"),
                    "title": s.get("title"),
                    "relevance_score": s.get("relevance_score")
                }
                for s in sources
            ])

            # Create Query record
            query_record = Query(
                user_id=current_user.id,
                query_text=query_request.query,
                answer_text=rag_response["answer"],
                sources_json=sources_json,
                response_time_ms=response_time_ms,
                sources_count=len(sources),
                cache_hit=cache_hit  # Task 6: Track cache hit in Query record
            )
            db.add(query_record)
            db.commit()
            db.refresh(query_record)

            # Create PerformanceMetric record (Task 6: AC#8 detailed metrics)
            metric = PerformanceMetric(
                query_id=query_record.id,
                retrieval_time_ms=retrieval_time_ms,
                llm_time_ms=llm_time_ms,
                total_time_ms=response_time_ms,
                cache_hit=cache_hit  # Task 6: Record actual cache_hit flag
            )
            db.add(metric)
            db.commit()

            logger.info(
                f"Query {query_record.id} stored successfully - "
                f"user: {current_user.id}, response_time: {response_time_ms:.2f}ms, "
                f"cache_hit: {cache_hit}"
            )
        except Exception as e:
            logger.error(f"Failed to store query metrics: {str(e)}")
            # Don't fail the response, just log the error

        # Log successful query (AC#7)
        logger.info(
            f"Query completed successfully for user {current_user.id}: "
            f"response_time: {response_time_ms:.2f}ms, "
            f"documents: {rag_response.get('documents_retrieved', 0)}, "
            f"cache_hit: {cache_hit}"
        )

        # Return response with rate limit headers
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ValueError as e:
        logger.warning(f"Invalid query request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000

        error_msg = f"Query processing failed: {str(e)}"
        logger.error(
            f"Query failed for user {current_user.id}: {error_msg} "
            f"(response_time: {response_time_ms:.2f}ms)"
        )

        raise HTTPException(
            status_code=500,
            detail="Query processing failed. Please try again later."
        )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="IA Service Metrics (Admin Only)",
    description="""Get aggregated metrics for the IA service over the last 24 hours. Admin access required.

**Task 10**: Implement Metrics Endpoint (3 hours)

Provides insights into system performance and usage patterns:
- Total query count in 24-hour window
- Response time distribution (avg, p50, p95, p99)
- Cache hit rate for query optimization
- Average documents retrieved per query

Requires ADMIN role. Non-admin users receive 403 Forbidden.
""",
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_queries": 156,
                        "avg_response_time_ms": 1245.7,
                        "p50_ms": 1100.0,
                        "p95_ms": 1950.0,
                        "p99_ms": 2100.0,
                        "cache_hit_rate": 0.15,
                        "avg_documents_retrieved": 2.8,
                        "period_hours": 24,
                        "generated_at": "2025-11-13T10:30:00Z"
                    }
                }
            }
        },
        403: {"description": "Forbidden - Admin access required"},
        500: {"description": "Metrics calculation error"}
    }
)
async def get_metrics(
    db=Depends(get_session),
    current_user=Depends(get_current_admin_user)
):
    """
    Get aggregated metrics for the IA service (admin only).

    AC#9: Returns aggregated metrics over the last 24 hours:
    - total_queries: Total number of queries processed
    - avg_response_time_ms: Average response time
    - p50/p95/p99_ms: Percentile response times
    - cache_hit_rate: Fraction of cache hits (0.0-1.0)
    - avg_documents_retrieved: Average docs per query

    Requires admin role for access.
    """
    from app.models.query import Query, PerformanceMetric
    from datetime import datetime, timedelta
    from sqlmodel import select, func
    import statistics

    start_time = time.time()

    try:
        # Calculate 24 hours ago
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(hours=24)

        logger.info(
            f"Calculating metrics for admin user {current_user.id} "
            f"from {period_start} to {now}"
        )

        # Query total number of queries in last 24 hours
        query_count_stmt = select(func.count()).select_from(Query)
        query_count_stmt = query_count_stmt.where(
            Query.created_at >= period_start
        )
        total_queries = db.exec(query_count_stmt).one()

        if total_queries == 0:
            # No data in the period, return zero metrics
            logger.info("No queries found in the last 24 hours")

            return MetricsResponse(
                total_queries=0,
                avg_response_time_ms=0.0,
                p50_ms=0.0,
                p95_ms=0.0,
                p99_ms=0.0,
                cache_hit_rate=0.0,
                avg_documents_retrieved=0.0,
                period_hours=24,
                generated_at=now
            )

        # Get all response times in the period
        response_times_stmt = select(Query.response_time_ms).where(
            Query.created_at >= period_start
        )
        response_times = db.exec(response_times_stmt).all()
        response_times = [float(rt) for rt in response_times if rt is not None]

        # Calculate average response time
        avg_response_time_ms = (
            sum(response_times) / len(response_times)
            if response_times
            else 0.0
        )

        # Calculate percentiles
        if len(response_times) >= 2:
            response_times_sorted = sorted(response_times)
            p50_idx = max(0, int(len(response_times_sorted) * 0.50) - 1)
            p95_idx = max(0, int(len(response_times_sorted) * 0.95) - 1)
            p99_idx = max(0, int(len(response_times_sorted) * 0.99) - 1)

            p50_ms = float(response_times_sorted[p50_idx])
            p95_ms = float(response_times_sorted[p95_idx])
            p99_ms = float(response_times_sorted[p99_idx])
        else:
            # If only 1 query, all percentiles are the same
            p50_ms = response_times[0] if response_times else 0.0
            p95_ms = response_times[0] if response_times else 0.0
            p99_ms = response_times[0] if response_times else 0.0

        # Get cache hit rate from PerformanceMetric
        cache_hits_stmt = select(func.count()).select_from(PerformanceMetric)
        cache_hits_stmt = cache_hits_stmt.where(
            PerformanceMetric.cache_hit == True,
            PerformanceMetric.created_at >= period_start
        )
        cache_hits = db.exec(cache_hits_stmt).one()

        cache_hit_rate = (
            cache_hits / total_queries
            if total_queries > 0
            else 0.0
        )

        # Get average documents retrieved
        avg_docs_stmt = select(func.avg(Query.sources_count)).where(
            Query.created_at >= period_start
        )
        avg_docs_retrieved = db.exec(avg_docs_stmt).one()
        avg_docs_retrieved = float(avg_docs_retrieved) if avg_docs_retrieved else 0.0

        metrics_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Metrics calculated successfully: "
            f"total_queries={total_queries}, "
            f"avg_response_time={avg_response_time_ms:.2f}ms, "
            f"p95={p95_ms:.2f}ms, "
            f"cache_hit_rate={cache_hit_rate:.2%}, "
            f"calc_time={metrics_time_ms:.2f}ms"
        )

        response = MetricsResponse(
            total_queries=total_queries,
            avg_response_time_ms=avg_response_time_ms,
            p50_ms=p50_ms,
            p95_ms=p95_ms,
            p99_ms=p99_ms,
            cache_hit_rate=cache_hit_rate,
            avg_documents_retrieved=avg_docs_retrieved,
            period_hours=24,
            generated_at=now
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        metrics_time_ms = (time.time() - start_time) * 1000

        error_msg = f"Metrics calculation failed: {str(e)}"
        logger.error(
            f"Metrics error for admin user {current_user.id}: {error_msg} "
            f"(calc_time: {metrics_time_ms:.2f}ms)"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to calculate metrics. Please try again later."
        )


# Story 4.1: Document Summary Generation Endpoint

@router.post(
    "/generate/summary",
    response_model=SummaryGenerationResponse,
    summary="Generate Document Summary",
    description="""Generate an automatic summary of any document in the repository (Story 4.1, AC1-AC13).

Provides quick understanding of key points without reading full document.

Supports three summary lengths:
- **short**: ~150 words
- **medium**: ~300 words
- **long**: ~500 words

Includes 24-hour intelligent caching to improve performance on repeated requests.
""",
    responses={
        200: {
            "description": "Summary generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "document_id": 1,
                        "document_title": "Política de Vacaciones Anuales",
                        "summary": "La compañía otorga 15 días hábiles de vacaciones anuales a todos los empleados...\n*Resumen generado automáticamente por IA. Revisa el documento completo para detalles precisos.*",
                        "summary_length": "medium",
                        "word_count": 289,
                        "generated_at": "2025-11-14T10:30:00Z",
                        "generation_time_ms": 2345.5
                    }
                }
            }
        },
        400: {
            "description": "Invalid request or document issue",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "El documento es demasiado corto para resumir. Léelo directamente."
                    }
                }
            }
        },
        401: {"description": "Unauthenticated - authentication required"},
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Documento no encontrado"}
                }
            }
        },
        429: {"description": "Rate limit exceeded"},
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "Servicio de IA no disponible"}
                }
            }
        }
    }
)
async def generate_summary(
    request: Request,
    summary_request: SummaryGenerationRequest,
    db=Depends(get_session),
    current_user=Depends(get_current_user)
):
    """
    Generate an automatic summary of a document.

    This endpoint implements the complete summary generation pipeline (Story 4.1):

    **AC1-AC3**: Endpoint with Bearer token authentication, request/response validation
    **AC4-AC6**: LLM-based generation with configurable length and parameters
    **AC7**: Appends AI disclaimer to all summaries
    **AC8-AC11**: Comprehensive error handling for all failure cases
    **AC12**: Intelligent 24-hour caching of summaries
    **AC13**: Automatic document truncation for very large documents

    Rate limiting: 10 summary requests per 60 seconds per user
    """
    from app.services.summary_service import SummaryService

    start_time = time.time()

    try:
        # Rate limiting (10 summaries per 60 seconds per user)
        user_rate_key = f"rate_limit:summary:{current_user.id}"
        now = time.time()

        if user_rate_key not in rate_limits:
            rate_limits[user_rate_key] = {"count": 0, "window_start": now}

        # Reset window if expired (60 seconds)
        if now - rate_limits[user_rate_key]["window_start"] > 60:
            rate_limits[user_rate_key] = {"count": 0, "window_start": now}

        # Check limit
        if rate_limits[user_rate_key]["count"] >= 10:
            logger.warning(
                f"Rate limit exceeded for summary generation - user {current_user.id}: "
                f"{rate_limits[user_rate_key]['count']} requests in current window"
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: 10 summary requests per 60 seconds per user"
            )

        # Increment counter
        rate_limits[user_rate_key]["count"] += 1

        logger.info(
            f"Summary request from user {current_user.id}: "
            f"document_id={summary_request.document_id}, "
            f"summary_length={summary_request.summary_length}"
        )

        # Check if LLM service is available
        llm_svc = OllamaLLMService()
        if not await llm_svc.health_check_async():
            logger.warning("Ollama service not available for summary generation")
            raise HTTPException(
                status_code=503,
                detail="Servicio de IA no disponible"
            )

        # Generate summary using SummaryService
        summary_service = SummaryService(db)
        result = await summary_service.generate_summary(
            document_id=summary_request.document_id,
            summary_length=summary_request.summary_length,
            user_id=current_user.id
        )

        # Build response
        response = SummaryGenerationResponse(
            document_id=result["document_id"],
            document_title=result["document_title"],
            summary=result["summary"],
            summary_length=result["summary_length"],
            word_count=result["word_count"],
            generated_at=result["generated_at"],
            generation_time_ms=result["generation_time_ms"]
        )

        total_time = (time.time() - start_time) * 1000

        logger.info(
            f"Summary generated successfully for document {summary_request.document_id} "
            f"(user: {current_user.id}, length: {summary_request.summary_length}, "
            f"time: {total_time:.0f}ms)"
        )

        return response

    except ValueError as e:
        # Input validation or document issues (AC8-AC10, AC13)
        error_msg = str(e)

        # Map to appropriate HTTP status codes
        if "no encontrado" in error_msg.lower():
            status_code = 404
            logger.warning(f"Document not found: {error_msg}")
        else:
            status_code = 400
            logger.warning(f"Invalid summary request: {error_msg}")

        raise HTTPException(status_code=status_code, detail=error_msg)

    except ConnectionError as e:
        # LLM service unavailable (AC11)
        logger.error(f"LLM service error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Servicio de IA no disponible"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        total_time = (time.time() - start_time) * 1000

        error_msg = f"Summary generation failed: {str(e)}"
        logger.error(
            f"Unexpected error during summary generation for user {current_user.id}: "
            f"{error_msg} (time: {total_time:.0f}ms)"
        )

        raise HTTPException(
            status_code=500,
            detail="Summary generation failed. Please try again later."
        )


# Story 4.2: Quiz Generation Endpoint

@router.post(
    "/generate/quiz",
    response_model=QuizGenerationResponse,
    summary="Generate Quiz from Document",
    description="""Generate multiple-choice quiz automatically from a document (Story 4.2, AC1-AC15).

Supports three difficulty levels and configurable question counts:
- **basic**: Recall-based questions (direct facts from document)
- **intermediate**: Application and comprehension questions (scenarios)
- **advanced**: Analysis and synthesis questions (complex reasoning)

Question counts: 5, 10, or 15 questions

Includes 7-day intelligent caching to improve performance on repeated requests.
""",
    responses={
        200: {
            "description": "Quiz generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "quiz_id": 42,
                        "questions": [
                            {
                                "question": "¿Cuál es el período de vacaciones?",
                                "options": ["15 días", "10 días", "20 días", "30 días"],
                                "correct_answer": "15 días",
                                "explanation": "La política establece 15 días hábiles...",
                                "difficulty": "basic"
                            }
                        ],
                        "total_questions": 5,
                        "difficulty": "basic",
                        "estimated_minutes": 5,
                        "generated_at": "2025-11-14T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request or quiz generation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No se pudo generar cantidad requerida de preguntas"
                    }
                }
            }
        },
        401: {"description": "Unauthenticated - authentication required"},
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Documento no encontrado"}
                }
            }
        },
        429: {"description": "Rate limit exceeded"},
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "Servicio de IA no disponible"}
                }
            }
        }
    }
)
async def generate_quiz(
    request: Request,
    quiz_request: QuizGenerationRequest,
    db=Depends(get_session),
    current_user=Depends(get_current_user)
):
    """
    Generate an automatic quiz from a document.

    This endpoint implements the complete quiz generation pipeline (Story 4.2):

    **AC1-AC3**: Endpoint with Bearer token authentication, request validation, response structure
    **AC4-AC7**: LLM-based generation with difficulty levels and answer validation
    **AC8-AC11**: Comprehensive error handling for all failure cases
    **AC12-AC13**: Database storage with quiz and question tables
    **AC14**: Intelligent 7-day caching of quizzes
    **AC15**: Automatic time estimation

    Rate limiting: 10 quiz requests per 60 seconds per user
    """
    from app.services.quiz_service import QuizService

    start_time = time.time()

    try:
        # Rate limiting (10 quizzes per 60 seconds per user)
        user_rate_key = f"rate_limit:quiz:{current_user.id}"
        now = time.time()

        if user_rate_key not in rate_limits:
            rate_limits[user_rate_key] = {"count": 0, "window_start": now}

        # Reset window if expired (60 seconds)
        if now - rate_limits[user_rate_key]["window_start"] > 60:
            rate_limits[user_rate_key] = {"count": 0, "window_start": now}

        # Check limit
        if rate_limits[user_rate_key]["count"] >= 10:
            logger.warning(
                f"Rate limit exceeded for quiz generation - user {current_user.id}: "
                f"{rate_limits[user_rate_key]['count']} requests in current window"
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: 10 quiz requests per 60 seconds per user"
            )

        # Increment counter
        rate_limits[user_rate_key]["count"] += 1

        logger.info(
            f"Quiz request from user {current_user.id}: "
            f"document_id={quiz_request.document_id}, "
            f"num_questions={quiz_request.num_questions}, "
            f"difficulty={quiz_request.difficulty}"
        )

        # Check if LLM service is available
        llm_svc = OllamaLLMService()
        if not await llm_svc.health_check_async():
            logger.warning("Ollama service not available for quiz generation")
            raise HTTPException(
                status_code=503,
                detail="Servicio de IA no disponible"
            )

        # Generate quiz using QuizService
        quiz_service = QuizService(db)
        result = await quiz_service.generate_quiz(
            document_id=quiz_request.document_id,
            num_questions=quiz_request.num_questions,
            difficulty=quiz_request.difficulty,
            user_id=current_user.id
        )

        # Build response
        response = QuizGenerationResponse(
            quiz_id=result["quiz_id"],
            questions=[
                {
                    "question": q["question"],
                    "options": q["options"],
                    "correct_answer": q["correct_answer"],
                    "explanation": q["explanation"],
                    "difficulty": q["difficulty"]
                }
                for q in result["questions"]
            ],
            total_questions=result["total_questions"],
            difficulty=result["difficulty"],
            estimated_minutes=result["estimated_minutes"],
            generated_at=datetime.fromisoformat(result["generated_at"])
        )

        total_time = (time.time() - start_time) * 1000

        logger.info(
            f"Quiz generated successfully for document {quiz_request.document_id} "
            f"(user: {current_user.id}, "
            f"difficulty: {quiz_request.difficulty}, "
            f"questions: {quiz_request.num_questions}, "
            f"time: {total_time:.0f}ms)"
        )

        return response

    except ValueError as e:
        # Input validation or document issues
        error_msg = str(e)

        # Map to appropriate HTTP status codes
        if "no encontrado" in error_msg.lower():
            status_code = 404
            logger.warning(f"Document not found: {error_msg}")
        else:
            status_code = 400
            logger.warning(f"Invalid quiz request: {error_msg}")

        raise HTTPException(status_code=status_code, detail=error_msg)

    except ConnectionError as e:
        # LLM service unavailable
        logger.error(f"LLM service error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Servicio de IA no disponible"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        total_time = (time.time() - start_time) * 1000

        error_msg = f"Quiz generation failed: {str(e)}"
        logger.error(
            f"Unexpected error during quiz generation for user {current_user.id}: "
            f"{error_msg} (time: {total_time:.0f}ms)"
        )

        raise HTTPException(
            status_code=500,
            detail="Quiz generation failed. Please try again later."
        )

# Story 4.3: Quiz Submission Endpoint

@router.post(
    "/quiz/{quiz_id}/submit",
    summary="Submit Quiz Answers and Get Score",
    description="""Submit answers to a quiz and receive evaluated results (Story 4.3, AC9-AC11).

Accepts user's answers and returns:
- Score (number of correct answers)
- Percentage (0-100)
- Pass status (percentage >= 70%)
- Detailed results for each question with explanations

The endpoint automatically stores attempt in quiz_attempts table for audit trail.
""",
    responses={
        200: {
            "description": "Quiz submitted successfully and evaluated",
        },
        400: {
            "description": "Invalid request or validation failed",
        },
        401: {"description": "Unauthenticated - authentication required"},
        404: {
            "description": "Quiz not found",
        }
    }
)
async def submit_quiz(
    request: Request,
    quiz_id: int,
    submission: QuizSubmissionRequest,
    db=Depends(get_session),
    current_user=Depends(get_current_user)
):
    """Submit quiz answers and receive scored results."""
    from app.services.quiz_service import QuizService
    
    start_time = time.time()
    
    try:
        logger.info(
            f"Quiz submission from user {current_user.id}: quiz_id={quiz_id}, "
            f"answers_count={len(submission.answers)}"
        )
        
        # Use QuizService to evaluate submission
        quiz_service = QuizService(db)
        result = await asyncio.to_thread(
            quiz_service.submit_quiz,
            quiz_id=quiz_id,
            user_id=current_user.id,
            answers=submission.answers
        )
        
        # Build response
        response_data = {
            "quiz_id": result["quiz_id"],
            "score": result["score"],
            "total_questions": result["total_questions"],
            "percentage": result["percentage"],
            "passed": result["passed"],
            "results": result["results"],
            "submitted_at": result["submitted_at"]
        }
        
        total_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Quiz {quiz_id} submitted successfully by user {current_user.id} "
            f"(score: {result['score']}/{result['total_questions']}, "
            f"percentage: {result['percentage']:.1f}%, "
            f"time: {total_time:.0f}ms)"
        )
        
        return response_data
        
    except ValueError as e:
        error_msg = str(e)
        
        if "no encontrado" in error_msg.lower() or "quiz" in error_msg.lower():
            status_code = 404
            logger.warning(f"Quiz not found or access denied: {error_msg}")
        elif "acceso denegado" in error_msg.lower():
            status_code = 403
            logger.warning(f"Access denied to quiz: {error_msg}")
        else:
            status_code = 400
            logger.warning(f"Invalid quiz submission: {error_msg}")
        
        raise HTTPException(status_code=status_code, detail=error_msg)
        
    except HTTPException:
        raise
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        error_msg = f"Quiz submission failed: {str(e)}"
        logger.error(
            f"Unexpected error during quiz submission for user {current_user.id}, "
            f"quiz {quiz_id}: {error_msg} (time: {total_time:.0f}ms)"
        )
        
        raise HTTPException(
            status_code=500,
            detail="Quiz submission failed. Please try again later."
        )


@router.post(
    "/generate/learning-path",
    response_model=LearningPathGenerationResponse,
    summary="Generate Personalized Learning Path",
    description="Generate a personalized learning path for a given topic and user skill level",
    responses={
        200: {
            "description": "Learning path generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "learning_path_id": 1,
                        "title": "Ruta de Aprendizaje: Procedimientos de Reembolsos",
                        "steps": [
                            {
                                "step_number": 1,
                                "title": "Conceptos Fundamentales",
                                "document_id": 5,
                                "why_this_step": "Establece los conceptos base necesarios",
                                "estimated_time_minutes": 20
                            }
                        ],
                        "total_steps": 4,
                        "estimated_time_hours": 1.5,
                        "user_level": "beginner",
                        "generated_at": "2025-11-14T10:45:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid request or insufficient documents found"},
        401: {"description": "Unauthorized - authentication required"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "AI service unavailable"}
    }
)
async def generate_learning_path(
    request: Request,
    learning_path_request: LearningPathGenerationRequest,
    db=Depends(get_session),
    current_user=Depends(get_current_user)
):
    """
    Generate a personalized learning path for a given topic.

    This endpoint creates an instructional sequence through documents
    tailored to the user's skill level (beginner/intermediate/advanced).

    The learning path includes:
    - Ordered sequence of documents to study
    - Pedagogical justification for each step
    - Estimated time for each step
    - Total estimated learning time

    AC1, AC2, AC18 (Story 4.4)
    """
    from app.services.learning_path_service import LearningPathService

    start_time = time.time()

    try:
        # Rate limiting: max 5 requests per user per day (AC2.5 in story)
        rate_limit_key = f"learning_path:{current_user.id}"
        if not check_rate_limit(request, limit=5, window=86400):  # 86400 = 1 day in seconds
            raise HTTPException(
                status_code=429,
                detail="Límite de generación de rutas alcanzado. Máximo 5 por día."
            )

        # Validate LLM service is healthy
        llm_svc = OllamaLLMService()
        is_healthy = await llm_svc.health_check_async()
        if not is_healthy:
            raise ConnectionError("Ollama service not responding")

        # Generate learning path
        service = LearningPathService(db)
        response = await service.generate_learning_path(
            topic=learning_path_request.topic,
            user_level=learning_path_request.user_level,
            user_id=current_user.id
        )

        total_time = (time.time() - start_time) * 1000
        logger.info(
            f"Learning path generated successfully for user {current_user.id}, "
            f"topic: '{learning_path_request.topic}', level: {learning_path_request.user_level}, "
            f"time: {total_time:.0f}ms"
        )

        return response

    except ValueError as e:
        # Input validation or insufficient documents
        total_time = (time.time() - start_time) * 1000
        error_msg = str(e)

        logger.warning(
            f"Learning path generation validation error for user {current_user.id}: {error_msg} "
            f"(time: {total_time:.0f}ms)"
        )

        raise HTTPException(
            status_code=400,
            detail=error_msg
        )

    except ConnectionError as e:
        total_time = (time.time() - start_time) * 1000
        error_msg = str(e)

        logger.error(
            f"LLM service error during learning path generation for user {current_user.id}: {error_msg} "
            f"(time: {total_time:.0f}ms)"
        )

        raise HTTPException(
            status_code=503,
            detail="Servicio de IA no disponible. Intenta más tarde."
        )

    except HTTPException:
        raise

    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        error_msg = f"Learning path generation failed: {str(e)}"

        logger.error(
            f"Unexpected error during learning path generation for user {current_user.id}: "
            f"{error_msg} (time: {total_time:.0f}ms)"
        )

        raise HTTPException(
            status_code=500,
            detail="Error al generar la ruta de aprendizaje. Por favor intenta más tarde."
        )


@router.get(
    "/learning-path/{path_id}",
    response_model=LearningPathGenerationResponse,
    summary="Retrieve Learning Path",
    description="Get a previously generated learning path by ID",
    responses={
        200: {"description": "Learning path retrieved successfully"},
        401: {"description": "Unauthorized - authentication required"},
        404: {"description": "Learning path not found"},
        403: {"description": "Access denied - you don't have permission to view this path"}
    }
)
async def get_learning_path(
    path_id: int,
    db=Depends(get_session),
    current_user=Depends(get_current_user)
):
    """
    Retrieve a previously generated learning path.

    Returns the learning path with all steps and estimated times.
    Users can only access their own learning paths.

    AC13, AC17 (Story 4.4)
    """
    from sqlmodel import select

    try:
        # Fetch learning path from database
        learning_path = db.exec(
            select(LearningPath).where(LearningPath.id == path_id)
        ).first()

        if not learning_path:
            logger.warning(
                f"Learning path {path_id} not found (requested by user {current_user.id})"
            )
            raise HTTPException(
                status_code=404,
                detail="Ruta de aprendizaje no encontrada"
            )

        # Verify user has access (own path only)
        if learning_path.user_id != current_user.id:
            logger.warning(
                f"Access denied to learning path {path_id} for user {current_user.id} "
                f"(owner: {learning_path.user_id})"
            )
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a esta ruta"
            )

        # Format response from stored content_json
        content = learning_path.content_json or {}

        # Parse JSON if it's a string
        if isinstance(content, str):
            import json
            content = json.loads(content)

        # Calculate estimated_time_hours if not in content
        estimated_time_hours = content.get("estimated_time_hours")
        if estimated_time_hours is None or estimated_time_hours == 0:
            # Calculate from steps' estimated_time_minutes
            steps = content.get("steps", [])
            total_minutes = sum(step.get("estimated_time_minutes", 0) for step in steps)
            estimated_time_hours = total_minutes / 60 if total_minutes > 0 else 0.1

        response = LearningPathGenerationResponse(
            learning_path_id=learning_path.id,
            title=content.get("title", f"Ruta de Aprendizaje: {learning_path.topic}"),
            steps=content.get("steps", []),
            total_steps=content.get("total_steps", len(content.get("steps", []))),
            estimated_time_hours=estimated_time_hours,
            user_level=learning_path.user_level,
            generated_at=learning_path.created_at.isoformat() + "Z"
        )

        logger.info(
            f"Learning path {path_id} retrieved successfully for user {current_user.id}"
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        error_msg = f"Failed to retrieve learning path: {str(e)}"
        logger.error(
            f"Unexpected error retrieving learning path {path_id} for user {current_user.id}: {error_msg}"
        )

        raise HTTPException(
            status_code=500,
            detail="Error al obtener la ruta de aprendizaje. Por favor intenta más tarde."
        )
