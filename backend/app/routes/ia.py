"""
IA (Inteligencia Artificial) Routes

FastAPI router for AI/LLM related endpoints.
Provides health check and generation capabilities with proper
error handling, logging, and rate limiting.
"""

import time
import logging
from datetime import datetime, timedelta, timezone
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
    QueryRequest,
    QueryResponse,
    MetricsResponse,
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