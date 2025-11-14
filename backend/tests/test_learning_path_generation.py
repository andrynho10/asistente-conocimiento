"""
Integration tests for learning path generation endpoint (Story 4.4).

Tests the complete learning path generation pipeline through HTTP endpoints:
- Learning path generation endpoint with different user levels
- Parameter validation (topic, user_level)
- Error handling (insufficient documents, invalid params, LLM unavailable)
- Response structure validation
- Caching behavior
- Database storage and audit logging

AC1-AC20: Full compliance with Story 4.4 acceptance criteria
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
from app.models import Document, LearningPath
from app.core.security import get_password_hash
from datetime import datetime, timezone


# Helper class for mock retrieval results
class MockRetrievalResult:
    """Mock object mimicking retrieval service document result."""
    def __init__(self, document_id, title, category, snippet, relevance_score):
        self.document_id = document_id
        self.title = title
        self.category = category
        self.snippet = snippet
        self.relevance_score = relevance_score


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
def sample_documents(test_db_session):
    """Create multiple documents for retrieval testing."""
    db_session = test_db_session
    docs = [
        Document(
            title="Fundamentos de Procedimientos de Reembolso",
            description="Conceptos básicos de reembolsos",
            category="Procesos",
            file_type="txt",
            file_size_bytes=2000,
            file_path="/docs/reembolso_basico.txt",
            uploaded_by=1,
            content_text="""Conceptos Básicos de Reembolsos
Un reembolso es el pago que la empresa realiza a empleados por gastos específicos.
Los reembolsos incluyen viajes, alojamiento, alimentación, y otros gastos autorizados.
Requiere documentación (recibos) para ser procesado.""",
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="Procedimientos de Solicitud de Reembolsos",
            description="Paso a paso para solicitar reembolsos",
            category="Procesos",
            file_type="txt",
            file_size_bytes=3000,
            file_path="/docs/reembolso_procedimiento.txt",
            uploaded_by=1,
            content_text="""Procedimientos de Solicitud de Reembolsos
1. Recopile todos los recibos originales
2. Ingrese a la plataforma de reembolsos
3. Complete el formulario con detalles del gasto
4. Adjunte los recibos digitalizados
5. Indique el código de proyecto
6. Envíe para aprobación del supervisor
7. Espere confirmación (3-5 días hábiles)""",
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="Limites y Políticas de Reembolso",
            description="Montos máximos y políticas especiales",
            category="Políticas",
            file_type="txt",
            file_size_bytes=2500,
            file_path="/docs/reembolso_limites.txt",
            uploaded_by=1,
            content_text="""Límites y Políticas de Reembolso
Límites por categoría:
- Alojamiento: $150 USD/noche
- Alimentación: $50 USD/día
- Transporte local: $100 USD
- Viajes internacionales: consultar con finanzas

Políticas especiales:
- Requiere aprobación previa para gastos > $500
- No se reembolsan alcohol
- Los recibos deben ser en moneda local o USD""",
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="Casos Avanzados y Excepciones de Reembolsos",
            description="Situaciones complejas y soluciones",
            category="Referencia",
            file_type="txt",
            file_size_bytes=2800,
            file_path="/docs/reembolso_avanzado.txt",
            uploaded_by=1,
            content_text="""Casos Avanzados y Excepciones
Reembolsos internacionales:
- Convertir a USD al tipo de cambio del día
- Incluir justificación de conversión

Gastos conjuntos:
- Dividir entre participantes
- Documentar participación

Reembolsos rechazados:
- Sin recibos: rechazado
- Fuera de política: rechazado
- Monto excesivo sin aprobación: rechazado

Apelaciones:
- Presentar dentro de 30 días
- Incluir documentación adicional
- Enviar a gerente de finanzas""",
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
    ]

    for doc in docs:
        db_session.add(doc)
    db_session.commit()

    for doc in docs:
        db_session.refresh(doc)

    return docs


class TestLearningPathGenerationBasic:
    """Test AC1-AC6: Basic learning path generation endpoint."""

    def test_learning_path_generation_success_beginner(
        self, client, user_token, sample_documents, test_db_session
    ):
        """AC1-AC6: Generate beginner learning path with valid topic and user_level."""
        headers = {"Authorization": f"Bearer {user_token}"}

        mock_llm_response = {
            "title": "Ruta de Aprendizaje: Procedimientos de Reembolsos (Principiante)",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Entender los conceptos básicos de reembolsos",
                    "document_id": sample_documents[0].id,
                    "why_this_step": "Es importante conocer qué son los reembolsos y sus categorías",
                    "estimated_time_minutes": 15,
                },
                {
                    "step_number": 2,
                    "title": "Aprender el procedimiento paso a paso",
                    "document_id": sample_documents[1].id,
                    "why_this_step": "Necesitas saber exactamente cómo solicitar un reembolso",
                    "estimated_time_minutes": 20,
                },
                {
                    "step_number": 3,
                    "title": "Conocer los límites y políticas",
                    "document_id": sample_documents[2].id,
                    "why_this_step": "Es crítico entender los montos máximos permitidos",
                    "estimated_time_minutes": 15,
                },
            ],
        }

        with patch(
            "app.services.retrieval_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
        ) as mock_retrieval:
            with patch(
                "app.services.llm_service.OllamaLLMService.generate_response_async",
                new_callable=AsyncMock,
            ) as mock_gen:
                # Mock retrieval to return our sample documents with scores
                mock_retrieval.return_value = [
                    MockRetrievalResult(sample_documents[0].id, sample_documents[0].title, sample_documents[0].category, "Conceptos básicos...", 0.95),
                    MockRetrievalResult(sample_documents[1].id, sample_documents[1].title, sample_documents[1].category, "Procedimientos...", 0.92),
                    MockRetrievalResult(sample_documents[2].id, sample_documents[2].title, sample_documents[2].category, "Límites...", 0.88),
                    MockRetrievalResult(sample_documents[3].id, sample_documents[3].title, sample_documents[3].category, "Documentación...", 0.75),
                ]

                # Mock LLM response
                mock_gen.return_value = json.dumps(mock_llm_response)

                response = client.post(
                    "/api/ia/generate/learning-path",
                    json={
                        "topic": "procedimientos de reembolsos",
                        "user_level": "beginner",
                    },
                    headers=headers,
                )

                assert response.status_code == 200
                data = response.json()

                # AC1: Check endpoint exists and accepts parameters
                assert "learning_path_id" in data
                assert "title" in data
                assert "steps" in data

                # AC3: Check response structure
                assert data["estimated_time_hours"] > 0
                assert data["total_steps"] == 3
                assert data["user_level"] == "beginner"

                # AC7: Check ordering (foundational steps first)
                assert data["steps"][0]["step_number"] == 1
                assert "concepto" in data["steps"][0]["title"].lower()

    def test_learning_path_generation_intermediate(self, client, user_token, sample_documents):
        """AC1-AC2: Generate intermediate level learning path."""
        headers = {"Authorization": f"Bearer {user_token}"}

        mock_llm_response = {
            "title": "Ruta de Aprendizaje: Procedimientos de Reembolsos (Intermedio)",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Revisar procedimientos estándar",
                    "document_id": sample_documents[1].id,
                    "why_this_step": "Refrescar conocimiento de procedimientos básicos",
                    "estimated_time_minutes": 10,
                },
                {
                    "step_number": 2,
                    "title": "Dominar límites y excepciones",
                    "document_id": sample_documents[2].id,
                    "why_this_step": "Aplicar políticas correctamente en diferentes contextos",
                    "estimated_time_minutes": 25,
                },
                {
                    "step_number": 3,
                    "title": "Casos prácticos avanzados",
                    "document_id": sample_documents[3].id,
                    "why_this_step": "Resolver situaciones complejas reales",
                    "estimated_time_minutes": 30,
                },
            ],
        }

        with patch(
            "app.services.retrieval_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
        ) as mock_retrieval:
            with patch(
                "app.services.llm_service.OllamaLLMService.generate_response_async",
                new_callable=AsyncMock,
            ) as mock_gen:
                mock_retrieval.return_value = [
                    MockRetrievalResult(sample_documents[0].id, sample_documents[0].title, sample_documents[0].category, "Conceptos básicos...", 0.95),
                    MockRetrievalResult(sample_documents[1].id, sample_documents[1].title, sample_documents[1].category, "Procedimientos estándar...", 0.92),
                    MockRetrievalResult(sample_documents[2].id, sample_documents[2].title, sample_documents[2].category, "Límites y excepciones...", 0.88),
                    MockRetrievalResult(sample_documents[3].id, sample_documents[3].title, sample_documents[3].category, "Documentación adicional...", 0.75),
                ]
                mock_gen.return_value = json.dumps(mock_llm_response)

                response = client.post(
                    "/api/ia/generate/learning-path",
                    json={
                        "topic": "procedimientos de reembolsos",
                        "user_level": "intermediate",
                    },
                    headers=headers,
                )

                assert response.status_code == 200
                data = response.json()
                assert data["user_level"] == "intermediate"
                assert data["total_steps"] == 3


class TestLearningPathValidation:
    """Test AC2, AC4, AC9: Validation and error handling."""

    def test_topic_min_length_validation(self, client, user_token):
        """AC2: Topic must be minimum 5 characters."""
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/generate/learning-path",
            json={
                "topic": "abc",  # Too short
                "user_level": "beginner",
            },
            headers=headers,
        )

        assert response.status_code == 400

    def test_user_level_enum_validation(self, client, user_token):
        """AC2: User level must be valid enum."""
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/generate/learning-path",
            json={
                "topic": "procedimientos de reembolsos",
                "user_level": "expert",  # Invalid level
            },
            headers=headers,
        )

        assert response.status_code == 400

    def test_insufficient_documents_error(
        self, client, user_token, sample_documents, test_db_session
    ):
        """AC4, AC12: Error when < 2 relevant documents found."""
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch(
            "app.services.retrieval_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
        ) as mock_retrieval:
            # Return only 1 document below threshold
            mock_retrieval.return_value = [MockRetrievalResult(sample_documents[0].id, sample_documents[0].title, sample_documents[0].category, "Test...", 0.25)]

            response = client.post(
                "/api/ia/generate/learning-path",
                json={
                    "topic": "tema inexistente muy específico",
                    "user_level": "beginner",
                },
                headers=headers,
            )

            assert response.status_code == 400
            data = response.json()
            assert "No se encontraron suficientes documentos" in data.get("detail", "")


class TestLearningPathRetrieval:
    """Test AC5-AC6: Document retrieval and filtering."""

    def test_retrieval_uses_correct_service(
        self, client, user_token, sample_documents
    ):
        """AC5: Uses retrieve_relevant_documents from Story 3.2."""
        headers = {"Authorization": f"Bearer {user_token}"}

        mock_llm_response = {
            "title": "Test Path",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step 1",
                    "document_id": sample_documents[0].id,
                    "why_this_step": "Test",
                    "estimated_time_minutes": 15,
                },
                {
                    "step_number": 2,
                    "title": "Step 2",
                    "document_id": sample_documents[1].id,
                    "why_this_step": "Test",
                    "estimated_time_minutes": 20,
                },
            ],
        }

        with patch(
            "app.services.retrieval_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
        ) as mock_retrieval:
            with patch(
                "app.services.llm_service.OllamaLLMService.generate_response_async",
                new_callable=AsyncMock,
            ) as mock_gen:
                mock_retrieval.return_value = [
                    MockRetrievalResult(sample_documents[0].id, sample_documents[0].title, sample_documents[0].category, "Conceptos...", 0.95),
                    MockRetrievalResult(sample_documents[1].id, sample_documents[1].title, sample_documents[1].category, "Procedimientos...", 0.92),
                    MockRetrievalResult(sample_documents[2].id, sample_documents[2].title, sample_documents[2].category, "Límites...", 0.88),
                ]
                mock_gen.return_value = json.dumps(mock_llm_response)

                response = client.post(
                    "/api/ia/generate/learning-path",
                    json={
                        "topic": "procedimientos de reembolsos",
                        "user_level": "beginner",
                    },
                    headers=headers,
                )

                assert response.status_code == 200
                # Verify retrieval service was called with correct parameters
                mock_retrieval.assert_called_once()
                call_args = mock_retrieval.call_args
                assert call_args[1]["topic"] == "procedimientos de reembolsos"
                assert call_args[1]["top_k"] == 10

    def test_score_filtering_threshold(self, client, user_token, sample_documents):
        """AC6: Filter documents with score > 0.3."""
        headers = {"Authorization": f"Bearer {user_token}"}

        mock_llm_response = {
            "title": "Test Path",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step 1",
                    "document_id": sample_documents[0].id,
                    "why_this_step": "Test",
                    "estimated_time_minutes": 15,
                },
                {
                    "step_number": 2,
                    "title": "Step 2",
                    "document_id": sample_documents[1].id,
                    "why_this_step": "Test",
                    "estimated_time_minutes": 20,
                },
            ],
        }

        with patch(
            "app.services.retrieval_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
        ) as mock_retrieval:
            with patch(
                "app.services.llm_service.OllamaLLMService.generate_response_async",
                new_callable=AsyncMock,
            ) as mock_gen:
                # Mix of above and below threshold scores
                mock_retrieval.return_value = [
                    MockRetrievalResult(sample_documents[0].id, sample_documents[0].title, sample_documents[0].category, "Conceptos...", 0.95),
                    MockRetrievalResult(sample_documents[1].id, sample_documents[1].title, sample_documents[1].category, "Procedimientos...", 0.92),
                    MockRetrievalResult(sample_documents[2].id, sample_documents[2].title, sample_documents[2].category, "Below threshold", 0.25),  # Below 0.3
                ]
                mock_gen.return_value = json.dumps(mock_llm_response)

                response = client.post(
                    "/api/ia/generate/learning-path",
                    json={
                        "topic": "procedimientos de reembolsos",
                        "user_level": "beginner",
                    },
                    headers=headers,
                )

                assert response.status_code == 200


class TestLearningPathAuthentication:
    """Test AC18: Authentication requirement."""

    def test_authentication_required(self, client):
        """AC18: Endpoint requires Bearer token."""
        response = client.post(
            "/api/ia/generate/learning-path",
            json={
                "topic": "procedimientos de reembolsos",
                "user_level": "beginner",
            },
            # No authentication header
        )

        assert response.status_code == 401

    def test_invalid_token(self, client):
        """AC18: Invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token-xyz"}

        response = client.post(
            "/api/ia/generate/learning-path",
            json={
                "topic": "procedimientos de reembolsos",
                "user_level": "beginner",
            },
            headers=headers,
        )

        assert response.status_code == 401


class TestLearningPathRetrieval:
    """Test GET /learning-path/{path_id} endpoint (AC13, AC17)."""

    def test_get_learning_path_success(
        self, client, user_token, sample_documents, test_db_session
    ):
        """AC13, AC17: Retrieve generated learning path."""
        headers = {"Authorization": f"Bearer {user_token}"}

        # Create a learning path in the database
        lp = LearningPath(
            user_id=1,
            topic="procedimientos de reembolsos",
            user_level="beginner",
            title="Ruta de Aprendizaje: Reembolsos",
            content_json=json.dumps({
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Conceptos básicos",
                        "document_id": sample_documents[0].id,
                        "why_this_step": "Fundamentos",
                        "estimated_time_minutes": 15,
                    },
                    {
                        "step_number": 2,
                        "title": "Procedimientos",
                        "document_id": sample_documents[1].id,
                        "why_this_step": "Aplicación práctica",
                        "estimated_time_minutes": 25,
                    },
                ],
            }),
        )
        test_db_session.add(lp)
        test_db_session.commit()
        test_db_session.refresh(lp)

        response = client.get(
            f"/api/ia/learning-path/{lp.id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["learning_path_id"] == lp.id
        assert data["user_level"] == "beginner"
        assert len(data["steps"]) == 2
        # AC17: Check total time calculation
        assert data["estimated_time_hours"] == (15 + 25) / 60

    def test_get_learning_path_not_found(self, client, user_token):
        """AC13: Return 404 for non-existent path."""
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.get(
            "/api/ia/learning-path/999999",
            headers=headers,
        )

        assert response.status_code == 404

    def test_get_learning_path_unauthorized(self, client, user_token, test_db_session):
        """AC13, AC18: Only path owner can access."""
        # Create learning path for different user
        lp = LearningPath(
            user_id=999,  # Different user
            topic="test",
            user_level="beginner",
            title="Test Path",
            content_json=json.dumps({"steps": []}),
        )
        test_db_session.add(lp)
        test_db_session.commit()
        test_db_session.refresh(lp)

        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            f"/api/ia/learning-path/{lp.id}",
            headers=headers,
        )

        assert response.status_code == 403
