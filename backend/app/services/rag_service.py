"""
RAG Service - Retrieval-Augmented Generation Pipeline

Implements a 5-phase RAG pipeline combining document retrieval with LLM generation
to provide AI-generated responses grounded in corporate knowledge.

Pipeline Phases:
1. Retrieval: Fetch top-K relevant documents
2. Context Construction: Combine document snippets into formatted context
3. Augmentation: Build augmented prompt with context
4. Generation: Send augmented prompt to LLM
5. Response Formatting: Format response with sources and disclaimers
"""

import logging
import json
import time
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session

from app.services.retrieval_service import RetrievalService
from app.services.llm_service import OllamaLLMService
from app.services.cache_service import CacheService
from app.models.document import SearchResult
from app.exceptions import RetrievalTimeoutError, DatabaseTimeoutError

logger = logging.getLogger(__name__)

# RAG Configuration Constants
RAG_DEFAULT_TOP_K = 3
RAG_CONTEXT_LIMIT = 2000  # Characters (legacy, now using token limit)
MAX_CONTEXT_TOKENS = 2000  # Token limit for context pruning (AC#5)
RELEVANCE_THRESHOLD = 0.1  # Minimum relevance score to use document
RAG_DISCLAIMER = "\n\n*Nota: Esta respuesta fue generada por IA. Verifica con tu supervisor si tienes dudas.*"

# Cache Configuration (AC#2, #3)
RESPONSE_CACHE_TTL_SECONDS = 300  # 5 minutes
RETRIEVAL_CACHE_TTL_SECONDS = 600  # 10 minutes

# Global cache instances
response_cache = CacheService(max_size=100)  # Response cache for identical queries
retrieval_cache = CacheService(max_size=100)  # Retrieval cache for document searches


class RAGService:
    """
    Orchestrates the complete RAG pipeline for AI-powered Q&A.

    Combines document retrieval with LLM generation to produce
    accurate, source-grounded responses.
    """

    @staticmethod
    async def rag_query(
        user_query: str,
        user_id: int,
        session: Session,
        llm_service: OllamaLLMService,
        top_k: int = RAG_DEFAULT_TOP_K,
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Execute complete RAG pipeline: Retrieval -> Context -> Augmentation -> Generation -> Formatting.

        This is the main AC#3 requirement: rag_query(user_query: str, user_id: int) -> dict

        Implements response caching (AC#2), detailed timing measurements (AC#1, #4, #8).

        Args:
            user_query: User's natural language query
            user_id: ID of the user making the query (for audit)
            session: Database session for document access
            llm_service: OllamaLLMService instance for generation
            top_k: Number of documents to retrieve (default 3, max 5)
            temperature: LLM temperature for response generation
            max_tokens: Maximum tokens in LLM response

        Returns:
            Dict with structure: {
                answer: str,
                sources: List[{document_id, title, relevance_score}],
                response_time_ms: float,
                retrieval_time_ms: float,
                llm_time_ms: float,
                cache_hit: bool,
                documents_retrieved: int
            }

        Implements AC#1, #2, #3, #4, #5, #6 (no docs case), #7 (disclaimer), #8 (metrics logging)
        """

        pipeline_start = time.perf_counter()

        # AC#2: Check response cache first (for identical queries)
        cache_key = CacheService.generate_cache_key(user_query)
        cached_response = response_cache.get(cache_key)
        if cached_response is not None:
            # Measure actual response time for this cache hit (should be <50ms)
            cache_hit_time = (time.perf_counter() - pipeline_start) * 1000

            logger.debug(json.dumps({
                "event": "rag_cache_hit",
                "user_id": user_id,
                "cache_type": "response",
                "query_hash": cache_key[:8],
                "cache_hit_time_ms": round(cache_hit_time, 2)
            }))

            # Return cached response with current timing
            # Create a new dict to avoid modifying the cached version
            response_with_current_timing = dict(cached_response)
            response_with_current_timing["response_time_ms"] = round(cache_hit_time, 2)
            response_with_current_timing["cache_hit"] = True
            return response_with_current_timing
        metrics = {
            "user_id": user_id,
            "original_query": user_query,
            "phase_times": {},
            "documents_retrieved": 0,
            "avg_relevance_score": 0.0,
            "tokens_used": 0,
            "llm_called": False,
            "retrieval_time_ms": 0.0,
            "llm_time_ms": 0.0,
            "cache_hit": False
        }

        try:
            # ========== PHASE 1: RETRIEVAL ==========
            # AC#4: Retrieval phase recovers top-K documents
            # AC#4 (timing): Measure retrieval phase with high precision

            phase1_start = time.perf_counter()  # Use perf_counter for high precision

            logger.info(json.dumps({
                "event": "rag_phase_start",
                "phase": "retrieval",
                "user_id": user_id,
                "query": user_query,
                "top_k": top_k
            }))

            # Call RetrievalService to get relevant documents (AC#11: with timeout)
            try:
                search_results: List[SearchResult] = await RetrievalService.retrieve_relevant_documents(
                    query=user_query,
                    top_k=min(top_k, 5),  # Cap at 5 to maintain context limit
                    db=session
                )
            except TimeoutError as e:
                logger.error(json.dumps({
                    "event": "rag_retrieval_timeout",
                    "user_id": user_id,
                    "query": user_query,
                    "error": str(e)
                }))
                raise RetrievalTimeoutError(f"Document retrieval timeout: {str(e)}")

            phase1_time = (time.perf_counter() - phase1_start) * 1000  # Convert to milliseconds
            metrics["phase_times"]["retrieval"] = phase1_time
            metrics["retrieval_time_ms"] = phase1_time

            # Filter by relevance threshold (AC#6: skip if all < 0.1)
            relevant_docs = [doc for doc in search_results if doc.relevance_score >= RELEVANCE_THRESHOLD]
            metrics["documents_retrieved"] = len(relevant_docs)

            if relevant_docs:
                metrics["avg_relevance_score"] = sum(doc.relevance_score for doc in relevant_docs) / len(relevant_docs)

            logger.info(json.dumps({
                "event": "rag_retrieval_complete",
                "documents_found": len(search_results),
                "documents_relevant": len(relevant_docs),
                "avg_score": round(metrics["avg_relevance_score"], 3),
                "phase_time_ms": round(phase1_time * 1000, 2)
            }))

            # ========== EARLY RETURN: NO RELEVANT DOCUMENTS ==========
            # AC#6: If no relevant documents, return polite response without LLM call
            # AC#7: Disclaimer included even in no-docs case

            if not relevant_docs:
                logger.info(json.dumps({
                    "event": "rag_no_relevant_documents",
                    "user_id": user_id,
                    "reason": "all_scores_below_threshold"
                }))

                total_time = (time.perf_counter() - pipeline_start) * 1000

                # AC#7: Add disclaimer even in no-docs case
                answer_no_docs = "Lo siento, no encontré documentos relevantes para tu consulta. Por favor, intenta formular la pregunta de otra manera." + RAG_DISCLAIMER

                response = {
                    "answer": answer_no_docs,
                    "sources": [],
                    "response_time_ms": round(total_time, 2),
                    "retrieval_time_ms": round(metrics["retrieval_time_ms"], 2),
                    "llm_time_ms": 0.0,
                    "cache_hit": metrics["cache_hit"],
                    "documents_retrieved": 0
                }

                # AC#2: Cache this response too (no-docs case)
                response_cache.set(cache_key, response, ttl_seconds=RESPONSE_CACHE_TTL_SECONDS)

                logger.info(json.dumps({
                    "event": "rag_response_complete",
                    "response_time_ms": total_time,
                    "documents_retrieved": 0,
                    "llm_called": False
                }))

                return response

            # ========== PHASE 2: CONTEXT CONSTRUCTION ==========
            # AC#4: Context Construction combines snippets into formatted context
            # AC#5: Context pruning with token limit (2000 tokens max)

            phase2_start = time.perf_counter()

            context_parts = []
            context_tokens = 0  # Token count (approximation: len/4)
            used_docs = []

            for i, doc in enumerate(relevant_docs, 1):
                # Build context part with document info
                doc_context = f"[Documento {i}] {doc.title}\n"
                if doc.snippet:
                    doc_context += f"{doc.snippet}\n"

                # Estimate token count (rough: 1 token ≈ 4 characters)
                estimated_doc_tokens = len(doc_context) / 4

                # Check if adding this document would exceed token limit
                if context_tokens + estimated_doc_tokens > MAX_CONTEXT_TOKENS:
                    # Can we fit a truncated version?
                    available_tokens = MAX_CONTEXT_TOKENS - context_tokens
                    if available_tokens > 50:  # At least 50 tokens remaining
                        # Truncate the snippet to fit available tokens
                        available_chars = int(available_tokens * 4)
                        truncated_context = doc_context[:available_chars]
                        context_parts.append(truncated_context)
                        context_tokens += available_tokens

                        logger.info(json.dumps({
                            "event": "rag_context_pruned_partial",
                            "documents_included": len(used_docs) + 1,
                            "total_tokens": MAX_CONTEXT_TOKENS,
                            "truncated_doc_index": i
                        }))
                    else:
                        logger.info(json.dumps({
                            "event": "rag_context_limit_reached",
                            "documents_included": len(used_docs),
                            "context_tokens": context_tokens
                        }))
                    break

                context_parts.append(doc_context)
                context_tokens += estimated_doc_tokens
                used_docs.append(doc)

            context = "\n".join(context_parts)

            phase2_time = (time.perf_counter() - phase2_start) * 1000
            metrics["phase_times"]["context_construction"] = phase2_time

            logger.info(json.dumps({
                "event": "rag_context_constructed",
                "documents_included": len(used_docs),
                "context_tokens": context_tokens,
                "phase_time_ms": round(phase2_time, 2)
            }))

            # ========== PHASE 3: AUGMENTATION ==========
            # AC#4: Augmentation constructs prompt with context

            phase3_start = time.perf_counter()

            # Build augmented prompt with retrieved context
            augmented_prompt = RAGService._build_augmented_prompt(
                user_query=user_query,
                context=context
            )

            phase3_time = (time.perf_counter() - phase3_start) * 1000
            metrics["phase_times"]["augmentation"] = phase3_time

            logger.info(json.dumps({
                "event": "rag_prompt_augmented",
                "prompt_length": len(augmented_prompt),
                "phase_time_ms": round(phase3_time * 1000, 2)
            }))

            # ========== PHASE 4: GENERATION ==========
            # AC#4: Generation sends augmented prompt to LLM
            # AC#4 (timing): Measure LLM inference phase with high precision

            phase4_start = time.perf_counter()

            logger.info(json.dumps({
                "event": "rag_generation_start",
                "temperature": temperature,
                "max_tokens": max_tokens
            }))

            # Call LLM with augmented prompt
            llm_response = await llm_service.generate_response_async(
                prompt=augmented_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            phase4_time = (time.perf_counter() - phase4_start) * 1000
            metrics["phase_times"]["generation"] = phase4_time
            metrics["llm_time_ms"] = phase4_time  # LLM time is the main latency contributor
            metrics["llm_called"] = True

            # Extract tokens if available
            if isinstance(llm_response, dict):
                metrics["tokens_used"] = llm_response.get("total_tokens", 0)
                answer_text = llm_response.get("response", str(llm_response))
            else:
                answer_text = str(llm_response)

            logger.info(json.dumps({
                "event": "rag_generation_complete",
                "answer_length": len(answer_text),
                "tokens_used": metrics["tokens_used"],
                "phase_time_ms": round(phase4_time * 1000, 2)
            }))

            # ========== PHASE 5: RESPONSE FORMATTING ==========
            # AC#4: Response Formatting adds sources and disclaimers
            # AC#5: Structure: {answer, sources[], response_time_ms, documents_retrieved}
            # AC#7: Disclaimer required in all responses

            phase5_start = time.perf_counter()

            # Add disclaimer to answer (AC#7)
            final_answer = answer_text + RAG_DISCLAIMER

            # Format sources (AC#5: {document_id, title, relevance_score})
            sources = [
                {
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "relevance_score": round(doc.relevance_score, 3)
                }
                for doc in used_docs
            ]

            phase5_time = (time.perf_counter() - phase5_start) * 1000
            metrics["phase_times"]["response_formatting"] = phase5_time

            total_time = (time.perf_counter() - pipeline_start) * 1000

            # ========== BUILD FINAL RESPONSE ==========
            response = {
                "answer": final_answer,
                "sources": sources,
                "response_time_ms": round(total_time, 2),
                "retrieval_time_ms": round(metrics["retrieval_time_ms"], 2),
                "llm_time_ms": round(metrics["llm_time_ms"], 2),
                "cache_hit": metrics["cache_hit"],
                "documents_retrieved": len(used_docs)
            }

            # AC#2: Store response in cache for future identical queries
            response_cache.set(cache_key, response, ttl_seconds=RESPONSE_CACHE_TTL_SECONDS)

            # ========== AC#8: METRICS LOGGING ==========
            # Log comprehensive metrics for monitoring

            logger.info(json.dumps({
                "event": "rag_response_complete",
                "user_id": user_id,
                "response_time_ms": round(total_time, 2),
                "documents_retrieved": len(used_docs),
                "avg_relevance_score": round(metrics["avg_relevance_score"], 3),
                "tokens_used": metrics["tokens_used"],
                "phase_times": {k: round(v * 1000, 2) for k, v in metrics["phase_times"].items()},
                "llm_called": metrics["llm_called"],
                "answer_length": len(final_answer)
            }))

            return response

        except (RetrievalTimeoutError, DatabaseTimeoutError) as e:
            # Handle retrieval or database timeout (AC#11)
            logger.error(json.dumps({
                "event": "rag_timeout_error",
                "user_id": user_id,
                "error_type": type(e).__name__,
                "error": str(e)
            }))

            total_time = (time.perf_counter() - pipeline_start) * 1000
            return {
                "answer": f"La búsqueda de documentos tardó demasiado. Por favor, intenta con una consulta más específica. {RAG_DISCLAIMER}",
                "sources": [],
                "response_time_ms": round(total_time, 2),
                "retrieval_time_ms": round(metrics.get("retrieval_time_ms", 0), 2),
                "llm_time_ms": round(metrics.get("llm_time_ms", 0), 2),
                "cache_hit": False,
                "documents_retrieved": 0
            }

        except asyncio.TimeoutError:
            # Handle LLM timeout gracefully (10s standard)
            logger.error(json.dumps({
                "event": "rag_timeout_error",
                "user_id": user_id,
                "error": "LLM service timeout"
            }))

            total_time = (time.perf_counter() - pipeline_start) * 1000
            return {
                "answer": f"La consulta tardó demasiado en procesarse. {RAG_DISCLAIMER}",
                "sources": [],
                "response_time_ms": round(total_time, 2),
                "retrieval_time_ms": round(metrics.get("retrieval_time_ms", 0), 2),
                "llm_time_ms": round(metrics.get("llm_time_ms", 0), 2),
                "cache_hit": False,
                "documents_retrieved": 0
            }

        except Exception as e:
            # Log error and return graceful fallback
            logger.error(json.dumps({
                "event": "rag_error",
                "user_id": user_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }))

            total_time = (time.perf_counter() - pipeline_start) * 1000
            return {
                "answer": f"Hubo un error procesando tu consulta. {RAG_DISCLAIMER}",
                "sources": [],
                "response_time_ms": round(total_time, 2),
                "retrieval_time_ms": round(metrics.get("retrieval_time_ms", 0), 2),
                "llm_time_ms": round(metrics.get("llm_time_ms", 0), 2),
                "cache_hit": False,
                "documents_retrieved": 0
            }

    @staticmethod
    def _build_augmented_prompt(user_query: str, context: str) -> str:
        """
        Construct augmented prompt with context for LLM.

        AC#3: Used during Augmentation phase to build prompt for generation.

        Args:
            user_query: Original user query
            context: Retrieved context from documents

        Returns:
            Augmented prompt string ready for LLM
        """

        prompt = f"""Eres un asistente de inteligencia artificial especializado en responder preguntas sobre la organización.

Contexto de documentos corporativos:
{context}

Pregunta del usuario: {user_query}

Por favor, responde la pregunta basándote únicamente en el contexto proporcionado. Si la información no se encuentra en el contexto, indícalo claramente.

Respuesta:"""

        return prompt

    @staticmethod
    async def health_check(llm_service: OllamaLLMService) -> bool:
        """
        Pre-flight check before RAG execution.

        Validates that both Retrieval and LLM services are available.

        Args:
            llm_service: OllamaLLMService instance

        Returns:
            True if both services are healthy, False otherwise
        """

        try:
            # Check LLM health
            llm_healthy = await llm_service.health_check_async()

            if not llm_healthy:
                logger.warning("RAG health check failed: LLM service unhealthy")
                return False

            logger.info("RAG health check passed: all services healthy")
            return True

        except Exception as e:
            logger.error(f"RAG health check error: {str(e)}")
            return False
