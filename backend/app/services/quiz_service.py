"""
Quiz Generation Service for Story 4.2

Handles automatic generation of multiple-choice quizzes from documents
using the LLM service with caching and retry logic.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from sqlmodel import Session, select, func
from app.models import Quiz, QuizQuestion, GeneratedContent, ContentType, Document, User
from app.services.llm_service import OllamaLLMService

logger = logging.getLogger(__name__)


class QuizService:
    """Service for generating quizzes from documents."""

    def __init__(self, session: Session):
        """Initialize QuizService with database session."""
        self.session = session
        self.llm_service = OllamaLLMService()

    async def generate_quiz(
        self,
        document_id: int,
        num_questions: int,
        difficulty: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Generate a quiz for a document with caching support.

        Args:
            document_id: ID of document to generate quiz from
            num_questions: Number of questions (5, 10, or 15)
            difficulty: Difficulty level (basic, intermediate, advanced)
            user_id: ID of user requesting quiz

        Returns:
            Dictionary with quiz_id, questions, and metadata

        Raises:
            ValueError: If document not found or invalid parameters
            ConnectionError: If LLM service unavailable
        """
        # Validate document exists (AC9)
        document = self.session.exec(
            select(Document).where(Document.id == document_id)
        ).first()

        if not document:
            raise ValueError("Documento no encontrado")

        # Check cache (AC14 - 7 day TTL)
        cached_quiz = await self._check_cache(
            document_id, difficulty, num_questions
        )
        if cached_quiz:
            logger.info(
                f"Quiz cache hit for doc {document_id}, "
                f"difficulty={difficulty}, questions={num_questions}"
            )
            return cached_quiz

        # Generate new quiz
        logger.info(
            f"Generating quiz for document {document_id}: "
            f"{num_questions} questions, {difficulty} difficulty"
        )

        questions = await self._generate_questions(
            document, num_questions, difficulty
        )

        # Check if we got enough valid questions (AC8)
        if len(questions) < num_questions:
            raise ValueError(
                f"No se pudo generar cantidad requerida de preguntas "
                f"(generadas: {len(questions)}, requeridas: {num_questions})"
            )

        # Store in database
        quiz = await self._save_quiz(
            document_id, user_id, difficulty, num_questions, questions
        )

        # Cache the quiz
        await self._cache_quiz(quiz, questions, document_id)

        return {
            "quiz_id": quiz.id,
            "questions": [self._format_question(q) for q in questions],
            "total_questions": len(questions),
            "difficulty": difficulty,
            "estimated_minutes": self._estimate_time(num_questions),
            "generated_at": quiz.created_at.isoformat()
        }

    async def _check_cache(
        self,
        document_id: int,
        difficulty: str,
        num_questions: int
    ) -> Optional[Dict[str, Any]]:
        """Check if quiz is cached and still valid (7 days)."""
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        cached = self.session.exec(
            select(GeneratedContent).where(
                GeneratedContent.document_id == document_id,
                GeneratedContent.content_type == ContentType.QUIZ,
                GeneratedContent.created_at >= seven_days_ago
            )
        ).first()

        if cached:
            content = cached.content_json
            # Verify it matches requested parameters
            if (content.get("difficulty") == difficulty and
                content.get("total_questions") == num_questions):
                return content

        return None

    async def _generate_questions(
        self,
        document: Document,
        num_questions: int,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions with retry logic (AC3, AC6)."""
        questions = []
        max_retries = 2
        failed_attempts = 0

        for i in range(num_questions):
            question_data = None
            retries = 0

            while retries < max_retries and question_data is None:
                try:
                    question_data = await self._generate_single_question(
                        document, difficulty, i + 1
                    )
                    if self._validate_question(question_data):
                        questions.append(question_data)
                        logger.info(
                            f"Generated question {i+1}/{num_questions} "
                            f"for difficulty={difficulty}"
                        )
                    else:
                        logger.warning(
                            f"Question {i+1} validation failed, retrying..."
                        )
                        question_data = None
                        retries += 1

                except Exception as e:
                    logger.warning(
                        f"Error generating question {i+1}: {e}, "
                        f"retry {retries+1}/{max_retries}"
                    )
                    retries += 1
                    await asyncio.sleep(2 ** retries)  # exponential backoff

            if question_data is None:
                failed_attempts += 1
                logger.warning(
                    f"Failed to generate question {i+1} after {max_retries} retries"
                )

        # If too many failures, raise error (AC11)
        if failed_attempts > num_questions * 0.2:  # Allow up to 20% failure
            raise ConnectionError(
                "Servicio de IA no disponible - demasiadas fallas"
            )

        return questions

    async def _generate_single_question(
        self,
        document: Document,
        difficulty: str,
        question_number: int
    ) -> Optional[Dict[str, Any]]:
        """Generate a single quiz question (AC4, AC5, AC6, AC7)."""
        prompt = self._build_prompt(document, difficulty, question_number)

        try:
            response = await self.llm_service.generate_response_async(
                prompt=prompt,
                temperature=0.5,  # AC6: temperature=0.5
                max_tokens=self._get_max_tokens(difficulty)
            )

            # Parse JSON response
            question_data = json.loads(response)

            # AC7: Validate correct answer is in document
            if not self._validate_answer_in_document(
                question_data.get("correct_answer", ""),
                document.content_text or ""
            ):
                logger.warning(
                    f"Answer validation failed for question {question_number}: "
                    f"answer not found in document"
                )
                return None

            return question_data

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            raise

    def _build_prompt(
        self,
        document: Document,
        difficulty: str,
        question_number: int
    ) -> str:
        """Build prompt for LLM based on difficulty level."""
        # Truncate content to 10k chars (AC3)
        content = (document.content_text or "")[:10000]

        if difficulty == "basic":
            return f"""Eres un especialista en crear preguntas de evaluación para verificar comprensión básica de documentos.

Genera UNA pregunta de selección múltiple de nivel BÁSICO que pruebe recall de un hecho directo del documento.

La pregunta debe:
- Ser clara y no ambigua
- Tener respuesta directa en el documento (textual)
- Incluir 4 opciones (A, B, C, D)
- Una y solo una respuesta correcta

DOCUMENTO:
{content}

Responde EXACTAMENTE en este formato JSON:
{{
  "question": "¿Cuál es...",
  "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
  "correct_answer": "Opción A",
  "explanation": "La respuesta correcta es 'Opción A' porque [referencia específica en documento]",
  "difficulty": "basic",
  "topic": "Tema relacionado"
}}"""

        elif difficulty == "intermediate":
            return f"""Eres un especialista en crear preguntas que evalúan comprensión y aplicación de conceptos.

Genera UNA pregunta de selección múltiple de nivel INTERMEDIO que requiera entender y aplicar contenido.

La pregunta debe:
- Presentar una situación o escenario común relacionado al documento
- Requerir aplicación del conocimiento, no solo recall
- Tener 4 opciones donde una es claramente correcta y otras son plausibles errores
- Explicación debe ayudar a entender por qué otra respuesta podría parecer correcta

DOCUMENTO:
{content}

Responde EXACTAMENTE en este formato JSON:
{{
  "question": "Si [escenario], ¿cuál es...",
  "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
  "correct_answer": "Opción B",
  "explanation": "La respuesta correcta es 'Opción B' porque [razonamiento basado en documento]. 'Opción A' es un error común porque...",
  "difficulty": "intermediate",
  "topic": "Tema relacionado"
}}"""

        else:  # advanced
            return f"""Eres un especialista en crear preguntas que evalúan análisis profundo y síntesis de información.

Genera UNA pregunta de selección múltiple de nivel AVANZADO que requiera análisis crítico.

La pregunta debe:
- Presentar un escenario complejo o un dilema
- Requerir síntesis de múltiples conceptos del documento
- Aplicación a contexto corporativo real
- Respuesta correcta requiere razonamiento, no lookup simple

DOCUMENTO:
{content}

Responde EXACTAMENTE en este formato JSON:
{{
  "question": "En una situación donde [contexto complejo], ¿cuál de las siguientes...",
  "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
  "correct_answer": "Opción C",
  "explanation": "La respuesta correcta es 'Opción C' porque [análisis profundo]. Esta situación ilustra el principio de [concepto] que es fundamental para [aplicación empresarial].",
  "difficulty": "advanced",
  "topic": "Tema relacionado"
}}"""

    def _get_max_tokens(self, difficulty: str) -> int:
        """Get max tokens based on difficulty (AC6)."""
        tokens = {"basic": 150, "intermediate": 180, "advanced": 200}
        return tokens.get(difficulty, 150)

    def _validate_question(self, question_data: Optional[Dict]) -> bool:
        """Validate question structure (AC4, AC7)."""
        if not question_data:
            return False

        required_fields = {"question", "options", "correct_answer", "explanation"}
        if not all(field in question_data for field in required_fields):
            return False

        # Check 4 options
        if len(question_data.get("options", [])) != 4:
            return False

        # Check correct_answer is in options
        if question_data["correct_answer"] not in question_data["options"]:
            return False

        return True

    def _validate_answer_in_document(
        self,
        answer: str,
        content: str
    ) -> bool:
        """Validate correct answer is found in document (AC7)."""
        # Simple text matching - could be enhanced
        return answer.lower() in content.lower()

    async def _save_quiz(
        self,
        document_id: int,
        user_id: int,
        difficulty: str,
        num_questions: int,
        questions: List[Dict[str, Any]]
    ) -> Quiz:
        """Save quiz and questions to database (AC12, AC13)."""
        # Create quiz record
        quiz = Quiz(
            document_id=document_id,
            user_id=user_id,
            title=f"Quiz - {num_questions} preguntas ({difficulty})",
            difficulty=difficulty,
            num_questions=num_questions,
            is_validated=True
        )
        self.session.add(quiz)
        self.session.flush()  # Get quiz.id

        # Create question records
        for q_data in questions:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question=q_data["question"],
                options_json=q_data["options"],
                correct_answer=q_data["correct_answer"],
                explanation=q_data["explanation"],
                difficulty=q_data.get("difficulty", difficulty),
                topic=q_data.get("topic")
            )
            self.session.add(question)

        self.session.commit()
        return quiz

    async def _cache_quiz(
        self,
        quiz: Quiz,
        questions: List[Dict[str, Any]],
        document_id: int
    ) -> None:
        """Cache quiz in generated_content (AC14)."""
        cache_entry = GeneratedContent(
            document_id=document_id,
            user_id=quiz.user_id,
            content_type=ContentType.QUIZ,
            content_json={
                "quiz_id": quiz.id,
                "questions": [self._format_question(q) for q in questions],
                "total_questions": quiz.num_questions,
                "difficulty": quiz.difficulty,
                "estimated_minutes": self._estimate_time(quiz.num_questions),
                "generated_at": quiz.created_at.isoformat()
            }
        )
        self.session.add(cache_entry)
        self.session.commit()

    def _format_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format question for response."""
        return {
            "question": question_data.get("question", ""),
            "options": question_data.get("options", []),
            "correct_answer": question_data.get("correct_answer", ""),
            "explanation": question_data.get("explanation", ""),
            "difficulty": question_data.get("difficulty", "basic")
        }

    def _estimate_time(self, num_questions: int) -> int:
        """Estimate time to complete quiz (AC15)."""
        return num_questions  # Simple 1 minute per question
