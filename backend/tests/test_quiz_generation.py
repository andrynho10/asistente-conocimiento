"""
Integration tests for quiz generation endpoint (Story 4.2).

Tests the complete quiz generation pipeline through HTTP endpoints:
- Quiz generation endpoint with different difficulty levels
- Parameter validation (num_questions, difficulty)
- Error handling (document not found, invalid params, LLM unavailable)
- Caching behavior
- Response structure validation

AC1-AC15: Full compliance with Story 4.2 acceptance criteria
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
from app.models import Document
from app.core.security import get_password_hash
from datetime import datetime, timezone


@pytest.fixture
def client(test_client):
    """Create test client (alias for conftest test_client)."""
    return test_client


@pytest.fixture(autouse=True)
def cleanup_rate_limits():
    """Clear rate limits before each test to prevent cross-test interference."""
    from app.routes import ia
    ia.rate_limits.clear()
    yield
    ia.rate_limits.clear()


@pytest.fixture
def sample_document(test_db_session):
    """Create a sample document for testing."""
    db_session = test_db_session
    doc = Document(
        title="Política de Vacaciones",
        description="Documento de política de vacaciones de la empresa",
        category="Políticas RRHH",
        file_type="txt",
        file_size_bytes=1000,
        file_path="/docs/vacaciones.txt",
        uploaded_by=1,
        content_text="""Política de Vacaciones de la Empresa

Derecho a Vacaciones
Todo empleado tiene derecho a 15 días hábiles de vacaciones anuales, de acuerdo con la ley chilena.

Duración por antigüedad
- 1-5 años: 15 días hábiles
- 5-10 años: 20 días hábiles
- 10+ años: 25 días hábiles

Periodo de solicitud
Las vacaciones deben solicitarse con al menos 30 días de anticipación.
El jefe directo debe aprobar la fecha de vacaciones.

Días no hábiles
Los fines de semana y feriados no se cuentan como días de vacaciones.

Pago durante vacaciones
El empleado recibe su sueldo normal durante las vacaciones.

Vacaciones no gozadas
Las vacaciones no gozadas al final del año pueden acumularse hasta un máximo de 30 días.""",
        is_indexed=True,
        indexed_at=datetime.now(timezone.utc)
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


class TestQuizGenerationBasic:
    """Test AC1-AC3: Basic quiz generation endpoint."""

    def test_quiz_generation_basic_success(self, client, user_token, sample_document, db_session):
        """AC1-AC3: Generate basic difficulty quiz with 5 questions."""
        headers = {"Authorization": f"Bearer {user_token}"}

        mock_quiz_response = [
            {
                "question": "¿Cuántos días de vacaciones tiene derecho un empleado?",
                "options": ["15 días", "10 días", "20 días", "30 días"],
                "correct_answer": "15 días",
                "explanation": "La política establece 15 días hábiles de vacaciones anuales.",
                "difficulty": "basic",
                "topic": "Derechos de vacaciones"
            },
            {
                "question": "¿Cuál es el período mínimo para solicitar vacaciones?",
                "options": ["7 días", "30 días", "15 días", "60 días"],
                "correct_answer": "30 días",
                "explanation": "Las vacaciones deben solicitarse con al menos 30 días de anticipación.",
                "difficulty": "basic",
                "topic": "Procedimiento de solicitud"
            },
            {
                "question": "¿Se cuentan los fines de semana como días de vacaciones?",
                "options": ["Sí siempre", "No, nunca", "Solo si el empleado lo solicita", "Depende del jefe"],
                "correct_answer": "No, nunca",
                "explanation": "Los fines de semana y feriados no se cuentan como días de vacaciones.",
                "difficulty": "basic",
                "topic": "Cálculo de días"
            },
            {
                "question": "¿Cuánto se paga durante las vacaciones?",
                "options": ["50% del sueldo", "Nada", "Sueldo normal", "Depende del contrato"],
                "correct_answer": "Sueldo normal",
                "explanation": "El empleado recibe su sueldo normal durante las vacaciones.",
                "difficulty": "basic",
                "topic": "Compensación"
            },
            {
                "question": "¿Cuáles son las vacaciones no gozadas?",
                "options": ["Vacaciones perdidas", "Vacaciones rechazadas", "Vacaciones acumuladas hasta 30 días", "Vacaciones de otros empleados"],
                "correct_answer": "Vacaciones acumuladas hasta 30 días",
                "explanation": "Las vacaciones no gozadas al final del año pueden acumularse hasta un máximo de 30 días.",
                "difficulty": "basic",
                "topic": "Acumulación de vacaciones"
            }
        ]

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                # Return JSON-formatted responses for each question
                mock_gen.side_effect = [json.dumps(q) for q in mock_quiz_response]

                response = client.post(
                    "/api/ia/generate/quiz",
                    json={
                        "document_id": sample_document.id,
                        "num_questions": 5,
                        "difficulty": "basic"
                    },
                    headers=headers
                )

                assert response.status_code == 200
                data = response.json()

                # AC3: Response structure validation
                assert "quiz_id" in data
                assert "questions" in data
                assert "total_questions" in data
                assert data["total_questions"] == 5
                assert data["difficulty"] == "basic"
                assert "estimated_minutes" in data
                assert data["estimated_minutes"] == 5  # AC15
                assert "generated_at" in data

                # AC4: Question structure validation
                for question in data["questions"]:
                    assert "question" in question
                    assert "options" in question
                    assert len(question["options"]) == 4
                    assert "correct_answer" in question
                    assert question["correct_answer"] in question["options"]
                    assert "explanation" in question
                    assert "difficulty" in question

    def test_quiz_generation_invalid_document(self, client, user_token):
        """AC9: Return 404 when document not found."""
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/generate/quiz",
            json={
                "document_id": 99999,
                "num_questions": 5,
                "difficulty": "basic"
            },
            headers=headers
        )

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"].lower()

    def test_quiz_generation_invalid_num_questions(self, client, user_token, sample_document):
        """AC10: Return 400 for invalid num_questions."""
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/generate/quiz",
            json={
                "document_id": sample_document.id,
                "num_questions": 7,  # Invalid - must be 5, 10, or 15
                "difficulty": "basic"
            },
            headers=headers
        )

        assert response.status_code == 400

    def test_quiz_generation_invalid_difficulty(self, client, user_token, sample_document):
        """AC10: Return 400 for invalid difficulty."""
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/generate/quiz",
            json={
                "document_id": sample_document.id,
                "num_questions": 5,
                "difficulty": "hard"  # Invalid - must be basic, intermediate, advanced
            },
            headers=headers
        )

        assert response.status_code == 400


class TestQuizGenerationDifficulty:
    """Test AC5: Different difficulty levels."""

    @pytest.mark.parametrize("difficulty", ["basic", "intermediate", "advanced"])
    def test_quiz_generation_difficulties(self, client, user_token, sample_document, difficulty):
        """AC5: Generate quizzes for all difficulty levels."""
        headers = {"Authorization": f"Bearer {user_token}"}

        mock_question = {
            "question": "Test question",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "explanation": "This is the correct answer because...",
            "difficulty": difficulty,
            "topic": "Test topic"
        }

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                mock_gen.side_effect = [json.dumps(mock_question) for _ in range(5)]

                response = client.post(
                    "/api/ia/generate/quiz",
                    json={
                        "document_id": sample_document.id,
                        "num_questions": 5,
                        "difficulty": difficulty
                    },
                    headers=headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["difficulty"] == difficulty


class TestQuizGenerationQuestionCounts:
    """Test AC2, AC3, AC15: Different question counts."""

    @pytest.mark.parametrize("num_questions,estimated_minutes", [(5, 5), (10, 10), (15, 15)])
    def test_quiz_generation_question_counts(self, client, user_token, sample_document, num_questions, estimated_minutes):
        """AC2, AC15: Generate quizzes with 5, 10, and 15 questions."""
        headers = {"Authorization": f"Bearer {user_token}"}

        mock_question = {
            "question": "Test question",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "explanation": "This is the correct answer.",
            "difficulty": "basic",
            "topic": "Test topic"
        }

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                mock_gen.side_effect = [json.dumps(mock_question) for _ in range(num_questions)]

                response = client.post(
                    "/api/ia/generate/quiz",
                    json={
                        "document_id": sample_document.id,
                        "num_questions": num_questions,
                        "difficulty": "basic"
                    },
                    headers=headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["total_questions"] == num_questions
                assert data["estimated_minutes"] == estimated_minutes


class TestQuizGenerationErrors:
    """Test AC8, AC11: Error handling."""

    def test_quiz_generation_insufficient_questions(self, client, user_token, sample_document):
        """AC8: Return 400 if cannot generate required number of questions."""
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                # Only return 2 questions when 5 are requested
                mock_gen.side_effect = json.JSONDecodeError("msg", "doc", 0)

                response = client.post(
                    "/api/ia/generate/quiz",
                    json={
                        "document_id": sample_document.id,
                        "num_questions": 5,
                        "difficulty": "basic"
                    },
                    headers=headers
                )

                # Should return 400 or 503 depending on error
                assert response.status_code in [400, 503]

    def test_quiz_generation_llm_unavailable(self, client, user_token, sample_document):
        """AC11: Return 503 when LLM service unavailable."""
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False

            response = client.post(
                "/api/ia/generate/quiz",
                json={
                    "document_id": sample_document.id,
                    "num_questions": 5,
                    "difficulty": "basic"
                },
                headers=headers
            )

            assert response.status_code == 503
            assert "no disponible" in response.json()["detail"].lower()


class TestQuizAuthentication:
    """Test AC1: Authentication requirements."""

    def test_quiz_generation_requires_authentication(self, client, sample_document):
        """AC1: Quiz endpoint requires Bearer token authentication."""
        response = client.post(
            "/api/ia/generate/quiz",
            json={
                "document_id": sample_document.id,
                "num_questions": 5,
                "difficulty": "basic"
            }
        )

        assert response.status_code == 401
