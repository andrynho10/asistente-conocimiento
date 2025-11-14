"""
Learning Path Generation Service for Story 4.4

Handles automatic generation of personalized learning paths from documents
using the LLM service with retrieval, caching, and instructional design principles.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from sqlmodel import Session, select
from app.models import (
    LearningPath,
    GeneratedContent,
    ContentType,
    Document,
    AuditLog,
    AuditAction,
    AuditResourceType
)
from app.services.llm_service import OllamaLLMService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class LearningPathService:
    """Service for generating personalized learning paths from documents."""

    def __init__(self, session: Session):
        """Initialize LearningPathService with database session."""
        self.session = session
        self.llm_service = OllamaLLMService()

    async def generate_learning_path(
        self,
        topic: str,
        user_level: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Generate a personalized learning path for a topic.

        Args:
            topic: Topic for the learning path (min 5 chars, max 200)
            user_level: User skill level (beginner, intermediate, advanced)
            user_id: ID of user requesting learning path

        Returns:
            Dictionary with learning_path_id, title, steps, and metadata

        Raises:
            ValueError: If validation fails or insufficient documents found
            ConnectionError: If LLM service unavailable
        """
        # Validate topic (AC1)
        if not topic or len(topic.strip()) < 5:
            raise ValueError("El tema debe tener al menos 5 caracteres")

        if len(topic.strip()) > 200:
            raise ValueError("El tema no puede exceder 200 caracteres")

        topic = topic.strip()

        # Validate user_level (AC1)
        valid_levels = ["beginner", "intermediate", "advanced"]
        if user_level not in valid_levels:
            raise ValueError(
                f"user_level debe ser uno de: {', '.join(valid_levels)}"
            )

        # Check cache (AC - 30 day TTL for learning paths)
        cached_path = await self._check_cache(topic, user_level)
        if cached_path:
            logger.info(
                f"Learning path cache hit for topic='{topic}', "
                f"level={user_level}"
            )
            return cached_path

        # Generate new learning path
        logger.info(
            f"Generating learning path for topic='{topic}', level={user_level}"
        )

        # Retrieve relevant documents (AC5)
        try:
            documents = await RetrievalService.retrieve_relevant_documents(
                query=topic,
                top_k=10,
                db=self.session
            )
        except Exception as e:
            logger.error(f"Error retrieving documents for learning path: {e}")
            raise ValueError(
                f"Error al buscar documentos sobre '{topic}'. "
                "Por favor, intenta con otro tema."
            )

        # Filter documents with score > 0.3 (AC6)
        filtered_docs = [doc for doc in documents if doc.relevance_score > 0.3]

        # Validate minimum 2 documents (AC4)
        if len(filtered_docs) < 2:
            raise ValueError(
                f"No se encontraron suficientes documentos sobre '{topic}'. "
                "Se requieren al menos 2 documentos relevantes. "
                "Intenta con otro tema o reformula la búsqueda."
            )

        logger.info(
            f"Found {len(filtered_docs)} relevant documents "
            f"(filtered from {len(documents)}) for learning path"
        )

        # Generate learning path using LLM
        learning_path_data = await self._generate_path(
            topic, user_level, filtered_docs
        )

        # Validate response structure
        self._validate_path_data(learning_path_data, filtered_docs)

        # Extract steps
        steps = self._extract_steps(learning_path_data)

        # Store in database (AC11)
        learning_path = await self._save_learning_path(
            user_id, topic, user_level, learning_path_data, steps
        )

        # Log audit event (AC19)
        await self._log_audit(user_id, learning_path.id, topic)

        # Cache the learning path (30 day TTL)
        await self._cache_learning_path(
            learning_path, steps, topic, user_level, user_id
        )

        # Build response
        total_time_minutes = sum(step["estimated_time_minutes"] for step in steps)
        total_time_hours = round(total_time_minutes / 60.0, 1)

        return {
            "learning_path_id": learning_path.id,
            "title": f"Ruta de Aprendizaje: {topic}",
            "steps": steps,
            "total_steps": len(steps),
            "estimated_time_hours": total_time_hours,
            "user_level": user_level,
            "generated_at": learning_path.created_at.isoformat()
        }

    async def _check_cache(
        self,
        topic: str,
        user_level: str
    ) -> Optional[Dict[str, Any]]:
        """Check if learning path is cached and still valid (30 days)."""
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        # Note: For learning paths, we cache based on topic + user_level
        # document_id can be nullable for topic-based content
        cached = self.session.exec(
            select(GeneratedContent).where(
                GeneratedContent.content_type == ContentType.LEARNING_PATH,
                GeneratedContent.created_at >= thirty_days_ago
            )
        ).all()

        # Check if any cached entry matches our topic and user_level
        for entry in cached:
            content = entry.content_json
            if (content.get("topic") == topic and
                content.get("user_level") == user_level):
                return content

        return None

    async def _generate_path(
        self,
        topic: str,
        user_level: str,
        documents: List[Any]
    ) -> Dict[str, Any]:
        """Generate learning path using LLM with instructional design (AC8)."""
        prompt = self._build_prompt(topic, user_level, documents)

        try:
            response = await self.llm_service.generate_response_async(
                prompt=prompt,
                temperature=0.5,  # Consistency while allowing creativity
                max_tokens=1000   # Enough for 2-8 steps with justifications
            )

            # Parse JSON response (AC9)
            learning_path_data = json.loads(response)
            return learning_path_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError(
                "Error al generar la ruta de aprendizaje: "
                "respuesta inválida del servicio de IA"
            )
        except Exception as e:
            logger.error(f"Error generating learning path: {e}")
            raise ConnectionError(
                "Servicio de IA no disponible. Por favor, intenta más tarde."
            )

    def _build_prompt(
        self,
        topic: str,
        user_level: str,
        documents: List[Any]
    ) -> str:
        """Build instructional design prompt for LLM (AC8)."""
        # Level-specific guidance (AC8)
        level_guidance = {
            "beginner": (
                "Enfócate en conceptos fundamentales. "
                "Prioriza documentos introductorios y generales. "
                "Progresión gradual desde lo básico a lo aplicado."
            ),
            "intermediate": (
                "Balancear teoría con casos prácticos. "
                "Incluye ejemplos de aplicación y procedimientos específicos. "
                "Asume conocimiento básico previo."
            ),
            "advanced": (
                "Incluir excepciones, optimizaciones y sinergias entre temas. "
                "Enfócate en casos complejos, análisis crítico y mejores prácticas. "
                "Profundiza en aspectos técnicos avanzados."
            )
        }

        guidance = level_guidance.get(user_level, level_guidance["beginner"])

        # Format documents for prompt
        docs_text = ""
        for idx, doc in enumerate(documents, 1):
            docs_text += f"""
Documento {idx}:
- ID: {doc.document_id}
- Título: {doc.title}
- Categoría: {doc.category}
- Relevancia: {doc.relevance_score:.2f}
- Extracto: {doc.snippet[:200]}...
"""

        prompt = f"""Eres un especialista en diseño instruccional que crea rutas de aprendizaje personalizadas.

Tu tarea es diseñar una secuencia óptima de aprendizaje para el siguiente tema y nivel de usuario.

TEMA: {topic}
NIVEL DE USUARIO: {user_level}

GUÍA PEDAGÓGICA PARA ESTE NIVEL:
{guidance}

DOCUMENTOS DISPONIBLES:
{docs_text}

INSTRUCCIONES:
1. Diseña una ruta de aprendizaje de 2 a 8 pasos
2. Cada paso debe usar UN documento de los listados arriba
3. Los pasos deben seguir una progresión lógica (de fundamentos a aplicación)
4. Justifica pedagógicamente por qué cada paso es importante
5. Estima tiempo realista de estudio (5-120 minutos por paso)
6. NO repitas documentos - cada documento puede usarse máximo una vez
7. Adapta la complejidad y profundidad al nivel del usuario

FORMATO DE RESPUESTA (JSON estricto):
{{
  "steps": [
    {{
      "step_number": 1,
      "title": "Título descriptivo del paso",
      "document_id": 123,
      "why_this_step": "Justificación pedagógica clara (ej: 'Establece fundamentos conceptuales necesarios antes de procedimientos')",
      "estimated_time_minutes": 20
    }},
    {{
      "step_number": 2,
      "title": "Siguiente paso lógico",
      "document_id": 456,
      "why_this_step": "Por qué este paso sigue al anterior",
      "estimated_time_minutes": 30
    }}
  ]
}}

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional antes o después."""

        return prompt

    def _validate_path_data(
        self,
        path_data: Dict[str, Any],
        available_docs: List[Any]
    ) -> None:
        """Validate learning path structure and content (AC9)."""
        # Check required fields
        if "steps" not in path_data:
            raise ValueError("Respuesta del LLM no contiene campo 'steps'")

        steps = path_data["steps"]

        # Check step count (AC4: 2-8 steps)
        if not isinstance(steps, list):
            raise ValueError("Campo 'steps' debe ser una lista")

        if len(steps) < 2:
            raise ValueError(
                "La ruta de aprendizaje debe tener al menos 2 pasos"
            )

        if len(steps) > 8:
            raise ValueError(
                "La ruta de aprendizaje no puede tener más de 8 pasos"
            )

        # Validate each step
        required_step_fields = {
            "step_number", "title", "document_id",
            "why_this_step", "estimated_time_minutes"
        }

        available_doc_ids = {doc.document_id for doc in available_docs}
        used_doc_ids = set()

        for idx, step in enumerate(steps, 1):
            # Check all required fields present
            missing_fields = required_step_fields - set(step.keys())
            if missing_fields:
                raise ValueError(
                    f"Paso {idx} falta campos requeridos: {missing_fields}"
                )

            # Validate step_number is sequential
            if step["step_number"] != idx:
                raise ValueError(
                    f"Paso {idx} tiene step_number incorrecto: "
                    f"{step['step_number']}"
                )

            # Validate document_id exists in available docs
            doc_id = step["document_id"]
            if doc_id not in available_doc_ids:
                raise ValueError(
                    f"Paso {idx} referencia documento inexistente: {doc_id}"
                )

            # Check for duplicate documents
            if doc_id in used_doc_ids:
                raise ValueError(
                    f"Paso {idx} usa documento duplicado: {doc_id}"
                )
            used_doc_ids.add(doc_id)

            # Validate estimated time is positive and reasonable
            time_minutes = step["estimated_time_minutes"]
            if not isinstance(time_minutes, (int, float)) or time_minutes <= 0:
                raise ValueError(
                    f"Paso {idx} tiene tiempo estimado inválido: {time_minutes}"
                )

            if time_minutes > 120:
                logger.warning(
                    f"Paso {idx} tiene tiempo muy largo: {time_minutes} minutos"
                )

            # Validate title and why_this_step are non-empty strings
            if not isinstance(step["title"], str) or not step["title"].strip():
                raise ValueError(f"Paso {idx} tiene título vacío o inválido")

            if (not isinstance(step["why_this_step"], str) or
                not step["why_this_step"].strip()):
                raise ValueError(
                    f"Paso {idx} tiene justificación vacía o inválida"
                )

    def _extract_steps(self, path_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and format steps from LLM response."""
        steps = []
        for step in path_data["steps"]:
            steps.append({
                "step_number": step["step_number"],
                "title": step["title"],
                "document_id": step["document_id"],
                "why_this_step": step["why_this_step"],
                "estimated_time_minutes": step["estimated_time_minutes"]
            })
        return steps

    async def _save_learning_path(
        self,
        user_id: int,
        topic: str,
        user_level: str,
        path_data: Dict[str, Any],
        steps: List[Dict[str, Any]]
    ) -> LearningPath:
        """Save learning path to database (AC11)."""
        # Create learning path record with complete content
        learning_path = LearningPath(
            user_id=user_id,
            topic=topic,
            user_level=user_level,
            content_json={
                "topic": topic,
                "user_level": user_level,
                "steps": steps,
                "total_steps": len(steps),
                "estimated_time_hours": round(
                    sum(s["estimated_time_minutes"] for s in steps) / 60.0, 1
                )
            }
        )
        self.session.add(learning_path)
        self.session.commit()
        self.session.refresh(learning_path)

        return learning_path

    async def _log_audit(
        self,
        user_id: int,
        learning_path_id: int,
        topic: str
    ) -> None:
        """Log learning path generation to audit log (AC19)."""
        audit_entry = AuditLog(
            user_id=user_id,
            action="generate_learning_path",
            resource_type="learning_path",
            resource_id=learning_path_id,
            details=f"Generated learning path for topic: {topic}"
        )
        self.session.add(audit_entry)
        self.session.commit()

    async def _cache_learning_path(
        self,
        learning_path: LearningPath,
        steps: List[Dict[str, Any]],
        topic: str,
        user_level: str,
        user_id: int
    ) -> None:
        """Cache learning path in generated_content (30 day TTL)."""
        # Use first document from steps as document_id for cache entry
        # (GeneratedContent requires document_id, use first step's document)
        first_doc_id = steps[0]["document_id"]

        total_time_hours = round(
            sum(s["estimated_time_minutes"] for s in steps) / 60.0, 1
        )

        cache_entry = GeneratedContent(
            document_id=first_doc_id,
            user_id=user_id,
            content_type=ContentType.LEARNING_PATH,
            content_json={
                "learning_path_id": learning_path.id,
                "title": f"Ruta de Aprendizaje: {topic}",
                "topic": topic,
                "user_level": user_level,
                "steps": steps,
                "total_steps": len(steps),
                "estimated_time_hours": total_time_hours,
                "generated_at": learning_path.created_at.isoformat()
            }
        )
        self.session.add(cache_entry)
        self.session.commit()
