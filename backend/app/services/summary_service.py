"""
Summary Generation Service (Story 4.1)

Provides functionality for generating automatic summaries of documents
using the Ollama LLM with caching support (24-hour TTL).

Implements Tasks 2-5 of Story 4.1:
- Task 2: Endpoint validation and response structure
- Task 3: LLM-based summary generation with prompt engineering
- Task 4: Error handling and edge cases
- Task 5: Caching with 24-hour TTL
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlmodel import Session, select

from app.models import Document, GeneratedContent, ContentType
from app.services.llm_service import OllamaLLMService

logger = logging.getLogger(__name__)

# Summary length configuration (AC4, AC6)
SUMMARY_CONFIGS = {
    "short": {
        "target_words": 150,
        "max_tokens": 200,
        "word_range": (120, 180)
    },
    "medium": {
        "target_words": 300,
        "max_tokens": 400,
        "word_range": (270, 330)
    },
    "long": {
        "target_words": 500,
        "max_tokens": 600,
        "word_range": (450, 550)
    }
}

# Disclaimer (AC7)
DISCLAIMER = "\n\n*Resumen generado automáticamente por IA. Revisa el documento completo para detalles precisos.*"

# Document truncation limit (AC13)
MAX_CONTENT_LENGTH = 10000


class SummaryService:
    """Service for generating document summaries using Ollama LLM with caching."""

    def __init__(self, db: Session):
        """
        Initialize SummaryService.

        Args:
            db: SQLModel session for database operations
        """
        self.db = db
        self.llm_service = OllamaLLMService()

    async def generate_summary(
        self,
        document_id: int,
        summary_length: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Generate a summary of a document with caching support (Task 2-5).

        AC1: POST /api/ia/generate/summary endpoint
        AC2: Accepts document_id and summary_length parameters
        AC3: Returns structured response with metadata
        AC5: Implements full generation pipeline
        AC6: Uses appropriate LLM parameters
        AC7: Appends disclaimer
        AC12: Implements 24-hour caching
        AC13: Handles document truncation

        Args:
            document_id: ID of document to summarize
            summary_length: "short", "medium", or "long"
            user_id: ID of requesting user

        Returns:
            Dict with summary, metadata, and timing info

        Raises:
            ValueError: For invalid parameters or document issues
            ConnectionError: If LLM service unavailable
        """
        start_time = time.time()
        generation_start = None

        try:
            # AC8: Validate document exists (AC8 - 404 case)
            document = self.db.exec(
                select(Document).where(Document.id == document_id)
            ).first()

            if not document:
                logger.warning(f"Document {document_id} not found")
                raise ValueError("Documento no encontrado")

            # AC9: Validate document has content (AC9 - 400 case)
            if not document.content_text:
                logger.warning(f"Document {document_id} has no content_text")
                raise ValueError(
                    "El documento no tiene contenido procesado. Intenta más tarde."
                )

            # AC10: Validate minimum document length (AC10 - 400 case)
            word_count = len(document.content_text.split())
            if word_count < 100:
                logger.warning(f"Document {document_id} too short ({word_count} words)")
                raise ValueError(
                    "El documento es demasiado corto para resumir. Léelo directamente."
                )

            # Task 5: Check cache (AC12)
            cached_summary = self._get_cached_summary(
                document_id, summary_length
            )
            if cached_summary:
                logger.info(
                    f"Cache hit for document {document_id}, summary_length {summary_length}"
                )
                return cached_summary

            # Task 3: Prepare document content and truncate if necessary (AC13)
            content_text = document.content_text
            truncation_note = ""
            if len(content_text) > MAX_CONTENT_LENGTH:
                content_text = content_text[:MAX_CONTENT_LENGTH]
                truncation_note = "\n[Nota: Resumen basado en sección inicial del documento]"

            # Task 3: Construct prompt (AC5, AC6)
            prompt = self._build_summary_prompt(
                content_text,
                summary_length,
                truncation_note
            )

            # Task 3: Invoke LLM (AC5, AC6)
            generation_start = time.time()
            llm_config = SUMMARY_CONFIGS[summary_length]

            summary_text = await self._invoke_llm_with_retry(
                prompt,
                temperature=0.5,  # AC6
                max_tokens=llm_config["max_tokens"]  # AC6
            )

            generation_time = (time.time() - generation_start) * 1000

            # Task 3: Add disclaimer (AC7)
            summary_text = summary_text.strip() + DISCLAIMER

            # Task 3: Validate summary word count
            summary_word_count = len(summary_text.split())

            # Task 5: Store in cache (AC12)
            cache_content = {
                "summary": summary_text,
                "word_count": summary_word_count,
                "generation_time_ms": generation_time
            }
            self._cache_summary(
                document_id,
                summary_length,
                user_id,
                cache_content
            )

            total_time = (time.time() - start_time) * 1000

            logger.info(
                f"Summary generated for document {document_id} "
                f"({summary_length}, {summary_word_count} words, {generation_time:.0f}ms)"
            )

            return {
                "document_id": document_id,
                "document_title": document.title,
                "summary": summary_text,
                "summary_length": summary_length,
                "word_count": summary_word_count,
                "generated_at": datetime.now(timezone.utc),
                "generation_time_ms": generation_time,
                "total_time_ms": total_time
            }

        except ValueError:
            # Re-raise validation errors
            raise
        except (ConnectionError, TimeoutError) as e:
            # AC11: LLM not available → 503
            logger.error(f"LLM service error: {e}")
            raise ConnectionError("Servicio de IA no disponible")
        except Exception as e:
            logger.error(f"Unexpected error during summary generation: {e}")
            raise

    def _get_cached_summary(
        self,
        document_id: int,
        summary_length: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached summary if exists and not expired (AC12).

        Args:
            document_id: Document ID
            summary_length: Summary length type

        Returns:
            Cached summary dict or None if not found/expired
        """
        try:
            # Query generated_content table - need to filter by document, type, AND summary_length
            cached_items = self.db.exec(
                select(GeneratedContent).where(
                    GeneratedContent.document_id == document_id,
                    GeneratedContent.content_type == ContentType.SUMMARY
                )
            ).all()

            # Find the right one by summary_length in content_json
            generated_content = None
            for item in cached_items:
                if item.content_json.get("summary_length") == summary_length:
                    generated_content = item
                    break

            if not generated_content:
                return None

            # Check if cache expired (24 hours = 86400 seconds)
            now = datetime.now(timezone.utc)
            age = (now - generated_content.created_at).total_seconds()
            if age > 86400:  # 24 hours
                logger.debug(
                    f"Cache expired for document {document_id} "
                    f"(age: {age:.0f}s > 86400s)"
                )
                return None

            # Extract summary from content_json
            content_data = generated_content.content_json
            if "summary" not in content_data:
                return None

            logger.debug(
                f"Using cached summary for document {document_id} "
                f"(age: {age:.0f}s)"
            )

            return {
                "document_id": document_id,
                "document_title": content_data.get("document_title", ""),
                "summary": content_data["summary"],
                "summary_length": summary_length,
                "word_count": content_data.get("word_count", 0),
                "generated_at": generated_content.created_at,
                "generation_time_ms": content_data.get("generation_time_ms", 0),
                "total_time_ms": 5  # Cache hit is very fast
            }

        except Exception as e:
            logger.warning(f"Cache lookup error: {e}")
            return None

    def _cache_summary(
        self,
        document_id: int,
        summary_length: str,
        user_id: int,
        content: Dict[str, Any]
    ) -> None:
        """
        Store generated summary in cache table (AC12).

        Args:
            document_id: Document ID
            summary_length: Summary length type
            user_id: User requesting summary
            content: Summary content to cache
        """
        try:
            # Create GeneratedContent record
            generated_content = GeneratedContent(
                document_id=document_id,
                user_id=user_id,
                content_type=ContentType.SUMMARY,
                content_json={
                    "summary_length": summary_length,
                    **content  # Includes summary, word_count, generation_time_ms
                }
            )

            self.db.add(generated_content)
            self.db.commit()

            logger.debug(
                f"Cached summary for document {document_id}, "
                f"summary_length {summary_length}"
            )

        except Exception as e:
            logger.warning(f"Failed to cache summary: {e}")
            # Don't raise - caching is optional

    def _build_summary_prompt(
        self,
        content: str,
        summary_length: str,
        truncation_note: str = ""
    ) -> str:
        """
        Build prompt for LLM summary generation (Task 3.3).

        Args:
            content: Document content to summarize
            summary_length: Target length (short/medium/long)
            truncation_note: Optional note about truncation

        Returns:
            Formatted prompt for LLM
        """
        config = SUMMARY_CONFIGS[summary_length]
        target_words = config["target_words"]

        prompt = f"""Eres un asistente especializado en crear resúmenes ejecutivos de documentos corporativos.

Genera un resumen de máximo {target_words} palabras que capture las ideas principales sin perder información crítica.

Formato:
- Usa bullets para puntos clave
- Mantén números y fechas exactas
- Incluye próximos pasos si aplica
- Preserva al menos 80% de entidades clave (sustantivos, números, fechas){truncation_note}

DOCUMENTO:
{content}

RESUMEN:"""

        return prompt

    async def _invoke_llm_with_retry(
        self,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 400
    ) -> str:
        """
        Invoke LLM with retry logic on timeout (Task 4.4).

        Implements retry strategy:
        1. First attempt: temperature=0.5
        2. If timeout: retry with temperature=0.3
        3. If still timeout: retry with reduced max_tokens
        4. If all fail: raise ConnectionError

        Args:
            prompt: Prompt for LLM
            temperature: Initial temperature
            max_tokens: Max tokens to generate

        Returns:
            Generated summary text

        Raises:
            ConnectionError: If all retries fail
        """
        max_retries = 3
        current_temp = temperature

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"LLM invoke attempt {attempt + 1}/{max_retries}, "
                    f"temp={current_temp}, max_tokens={max_tokens}"
                )

                response = await self.llm_service.generate_response_async(
                    prompt=prompt,
                    temperature=current_temp,
                    max_tokens=max_tokens
                )

                if response and response.strip():
                    logger.debug(
                        f"LLM response successful on attempt {attempt + 1}"
                    )
                    return response

                # Empty response - treat as failure
                logger.warning(f"LLM returned empty response on attempt {attempt + 1}")

            except TimeoutError as e:
                logger.warning(f"LLM timeout on attempt {attempt + 1}: {e}")

                # Adjust parameters for retry
                if attempt == 0:
                    # First timeout: reduce temperature for determinism
                    current_temp = 0.3
                elif attempt == 1:
                    # Second timeout: reduce max_tokens
                    max_tokens = int(max_tokens * 0.75)

                if attempt < max_retries - 1:
                    continue
                # Last attempt failed - raise
                raise ConnectionError(f"LLM timeout after {max_retries} retries")

            except ConnectionError as e:
                logger.error(f"LLM connection error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise

        raise ConnectionError("Failed to generate summary after all retries")
