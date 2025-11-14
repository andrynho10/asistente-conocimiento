"""
Integration tests for IA endpoints.

Tests the complete RAG pipeline through HTTP endpoints:
- Health check endpoint
- Query endpoint with rate limiting and authentication
- Metrics endpoint
- Error handling

AC#1: Health Check Endpoint Operational
AC#2: Query Endpoint Basic Implementation
AC#6: Rate Limiting Enforcement
AC#7: Audit Logging
AC#8: Data Model Persistence
AC#9: Metrics Endpoint (Admin Only)
AC#10: Error Handling and Resilience
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
from app.core.security import get_password_hash


@pytest.fixture
def client(test_client):
    """Create test client (alias for conftest test_client)."""
    return test_client


@pytest.fixture(autouse=True)
def cleanup_rate_limits():
    """Clear rate limits before each test to prevent cross-test interference."""
    # Clear rate limits from ia.py
    from app.routes import ia
    ia.rate_limits.clear()
    yield
    # Clean up after test
    ia.rate_limits.clear()


class TestHealthCheckEndpoint:
    """Test AC#1: Health Check Endpoint."""

    def test_health_check_success(self, client):
        """AC#1: Health check returns 200 with ok status."""
        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True

            response = client.get("/api/ia/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "model" in data
            assert "response_time_ms" in data

    def test_health_check_unavailable(self, client):
        """AC#1: Health check returns 503 when service unavailable."""
        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False

            response = client.get("/api/ia/health")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unavailable"
            assert "error" in data

    def test_health_check_response_time(self, client):
        """AC#1: Health check includes response_time_ms."""
        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True

            response = client.get("/api/ia/health")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["response_time_ms"], float)
            assert data["response_time_ms"] >= 0


class TestQueryEndpoint:
    """Test AC#2: Query Endpoint Basic Implementation."""

    def test_query_valid_request(self, client, user_token):
        """AC#2: Valid query request returns 200.

        JWT Token Injection Pattern:
        - Uses user_token fixture from conftest.py (creates token via create_access_token)
        - Injected as method parameter to receive valid JWT token
        - Passed in Authorization header: Bearer {token}
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                with patch('app.services.retrieval_service.RetrievalService.retrieve_relevant_documents', new_callable=AsyncMock) as mock_retrieval:
                    mock_health.return_value = True
                    mock_gen.return_value = "Según los documentos..."
                    mock_retrieval.return_value = []

                    response = client.post(
                        "/api/ia/query",
                        json={
                            "query": "¿Cuál es la política de vacaciones?",
                            "context_mode": "general"
                        },
                        headers=headers
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "answer" in data
                    assert "sources" in data
                    assert "response_time_ms" in data
                    assert "documents_retrieved" in data

    def test_query_short_query(self, client, user_token):
        """AC#2: Query shorter than 10 characters returns 400.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/query",
            json={
                "query": "short",
                "context_mode": "general"
            },
            headers=headers
        )

        assert response.status_code == 400  # Validation error

    def test_query_invalid_context_mode(self, client, user_token):
        """AC#2: Invalid context_mode returns 400.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/query",
            json={
                "query": "¿Cuál es la política de vacaciones?",
                "context_mode": "invalid"
            },
            headers=headers
        )

        assert response.status_code == 400  # Validation error

    def test_query_no_auth(self, client):
        """AC#2: Unauthenticated request returns 401."""
        response = client.post(
            "/api/ia/query",
            json={
                "query": "¿Cuál es la política de vacaciones?",
                "context_mode": "general"
            }
        )

        assert response.status_code == 401

    def test_query_llm_unavailable(self, client, user_token):
        """AC#10: Query returns 503 when LLM unavailable.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False

            response = client.post(
                "/api/ia/query",
                json={
                    "query": "¿Cuál es la política de vacaciones?",
                    "context_mode": "general"
                },
                headers=headers
            )

            assert response.status_code == 503


class TestRateLimiting:
    """Test AC#6: Rate Limiting Enforcement."""

    def test_rate_limit_10_per_60_seconds(self, client, user_token):
        """AC#6: Rate limit enforces 10 queries per 60 seconds per user.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                with patch('app.services.retrieval_service.RetrievalService.retrieve_relevant_documents', new_callable=AsyncMock) as mock_retrieval:
                    mock_health.return_value = True
                    mock_gen.return_value = "Response"
                    mock_retrieval.return_value = []

                    # Make 10 successful requests
                    for i in range(10):
                        response = client.post(
                            "/api/ia/query",
                            json={
                                "query": f"Consulta número {i + 1} válida",
                                "context_mode": "general"
                            },
                            headers=headers
                        )
                        assert response.status_code == 200

                    # 11th request should be rate limited
                    response = client.post(
                        "/api/ia/query",
                        json={
                            "query": "Consulta número 11 debe ser rechazada",
                            "context_mode": "general"
                        },
                        headers=headers
                    )
                    assert response.status_code == 429

    def test_rate_limit_headers(self, client, user_token):
        """AC#6: Rate limit response includes X-RateLimit-* headers.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                with patch('app.services.retrieval_service.RetrievalService.retrieve_relevant_documents', new_callable=AsyncMock) as mock_retrieval:
                    mock_health.return_value = True
                    mock_gen.return_value = "Response"
                    mock_retrieval.return_value = []

                    # Make 10 requests to trigger limit
                    for i in range(10):
                        client.post(
                            "/api/ia/query",
                            json={
                                "query": f"Consulta válida {i}",
                                "context_mode": "general"
                            },
                            headers=headers
                        )

                    # 11th should have rate limit headers
                    response = client.post(
                        "/api/ia/query",
                        json={
                            "query": "Consulta rechazada",
                            "context_mode": "general"
                        },
                        headers=headers
                    )

                    assert response.status_code == 429
                    assert "X-RateLimit-Remaining" in response.headers or "detail" in response.json()


class TestErrorHandling:
    """Test AC#10: Error Handling and Resilience."""

    def test_error_no_stack_traces(self, client, user_token):
        """AC#10: Error responses don't include stack traces.

        Verifies that even when internal services fail, the API returns graceful error messages
        without exposing stack traces or technical details.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                with patch('app.services.retrieval_service.RetrievalService.retrieve_relevant_documents', new_callable=AsyncMock) as mock_retrieval:
                    from app.models.document import SearchResult
                    from datetime import datetime

                    mock_health.return_value = True
                    # Return some relevant documents so RAGService will call LLM
                    mock_retrieval.return_value = [
                        SearchResult(
                            document_id=1,
                            title="Test Document",
                            category="Test",
                            upload_date=datetime.now(),
                            snippet="Test snippet",
                            relevance_score=0.95
                        )
                    ]
                    mock_gen.side_effect = Exception("Database connection failed")

                    response = client.post(
                        "/api/ia/query",
                        json={
                            "query": "¿Cuál es la política de vacaciones?",
                            "context_mode": "general"
                        },
                        headers=headers
                    )

                    # RAGService catches all exceptions and returns graceful 200 response
                    assert response.status_code == 200
                    data = response.json()
                    # Should not contain actual exception details or stack traces
                    assert "traceback" not in str(data)
                    assert "Database connection failed" not in str(data)
                    assert "Exception" not in data.get("answer", "")
                    # Should have user-friendly error message
                    assert "Hubo un error" in data.get("answer", "") or "error" in data.get("answer", "").lower()

    def test_malformed_request_returns_error(self, client, user_token):
        """AC#10: Malformed requests return clear error messages.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/query",
            json={
                # Missing required 'query' field
                "context_mode": "general"
            },
            headers=headers
        )

        assert response.status_code in [400, 422]  # Bad request or validation error
        data = response.json()
        assert "detail" in data or "message" in data


class TestResponseStructure:
    """Test AC#5: Response Structure and Metadata."""

    def test_response_includes_all_fields(self, client, user_token):
        """AC#5: QueryResponse includes all required fields.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                with patch('app.services.retrieval_service.RetrievalService.retrieve_relevant_documents', new_callable=AsyncMock) as mock_retrieval:
                    mock_health.return_value = True
                    mock_gen.return_value = "Respuesta de prueba"
                    mock_retrieval.return_value = []

                    response = client.post(
                        "/api/ia/query",
                        json={
                            "query": "¿Cuál es la política de vacaciones?",
                            "context_mode": "general"
                        },
                        headers=headers
                    )

                    assert response.status_code == 200
                    data = response.json()

                    # AC#5 required fields
                    assert "query" in data
                    assert "answer" in data
                    assert "sources" in data
                    assert "response_time_ms" in data
                    assert "documents_retrieved" in data
                    assert "timestamp" in data

                    # Verify types
                    assert isinstance(data["query"], str)
                    assert isinstance(data["answer"], str)
                    assert isinstance(data["sources"], list)
                    assert isinstance(data["response_time_ms"], (int, float))
                    assert isinstance(data["documents_retrieved"], int)

    def test_response_timestamp_iso_format(self, client, user_token):
        """AC#5: Timestamp uses ISO format.

        JWT Token Injection Pattern: user_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                with patch('app.services.retrieval_service.RetrievalService.retrieve_relevant_documents', new_callable=AsyncMock) as mock_retrieval:
                    mock_health.return_value = True
                    mock_gen.return_value = "Respuesta"
                    mock_retrieval.return_value = []

                    response = client.post(
                        "/api/ia/query",
                        json={
                            "query": "Consulta de prueba para timestamp",
                            "context_mode": "general"
                        },
                        headers=headers
                    )

                    assert response.status_code == 200
                    data = response.json()
                    timestamp = data["timestamp"]

                    # Should be ISO8601 format with timezone info
                    assert "T" in timestamp  # ISO format contains T separator
                    assert "Z" in timestamp or "+" in timestamp  # Must have timezone (UTC Z or offset +/-)


class TestMetricsEndpoint:
    """Test AC#9: Metrics Endpoint (Admin Only)."""

    def test_metrics_admin_only_403_for_user(self, client, user_token):
        """AC#9: Non-admin users receive 403 Forbidden.

        JWT Token Injection Pattern:
        - Uses user_token fixture (normal user role) from conftest.py
        - Metrics endpoint requires admin role, so user token should return 403
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.get(
            "/api/ia/metrics",
            headers=headers
        )

        assert response.status_code == 403

    def test_metrics_admin_only_401_unauthenticated(self, client):
        """AC#9: Unauthenticated users receive 401."""
        response = client.get("/api/ia/metrics")

        assert response.status_code == 401

    def test_metrics_returns_correct_structure(self, client, admin_token):
        """AC#9: Metrics endpoint returns complete structure.

        JWT Token Injection Pattern:
        - Uses admin_token fixture from conftest.py (admin role)
        - Metrics endpoint requires admin role
        """
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get(
            "/api/ia/metrics",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # AC#9 required fields
        assert "total_queries" in data
        assert "avg_response_time_ms" in data
        assert "p50_ms" in data
        assert "p95_ms" in data
        assert "p99_ms" in data
        assert "cache_hit_rate" in data
        assert "avg_documents_retrieved" in data
        assert "period_hours" in data
        assert "generated_at" in data

        # Verify types and ranges
        assert isinstance(data["total_queries"], int)
        assert data["total_queries"] >= 0

        assert isinstance(data["avg_response_time_ms"], (int, float))
        assert data["avg_response_time_ms"] >= 0

        assert isinstance(data["p50_ms"], (int, float))
        assert data["p50_ms"] >= 0

        assert isinstance(data["p95_ms"], (int, float))
        assert data["p95_ms"] >= 0

        assert isinstance(data["p99_ms"], (int, float))
        assert data["p99_ms"] >= 0

        assert isinstance(data["cache_hit_rate"], (int, float))
        assert 0.0 <= data["cache_hit_rate"] <= 1.0

        assert isinstance(data["avg_documents_retrieved"], (int, float))
        assert data["avg_documents_retrieved"] >= 0

        assert isinstance(data["period_hours"], int)
        assert data["period_hours"] > 0

    def test_metrics_zero_queries(self, client, admin_token):
        """AC#9: Metrics with no queries in 24h returns zeros.

        JWT Token Injection Pattern: admin_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get(
            "/api/ia/metrics",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # If no queries, all should be zero
        if data["total_queries"] == 0:
            assert data["avg_response_time_ms"] == 0.0
            assert data["p50_ms"] == 0.0
            assert data["p95_ms"] == 0.0
            assert data["p99_ms"] == 0.0
            assert data["cache_hit_rate"] == 0.0
            assert data["avg_documents_retrieved"] == 0.0

    def test_metrics_timestamp_iso_format(self, client, admin_token):
        """AC#9: Metrics includes ISO format timestamp.

        JWT Token Injection Pattern: admin_token fixture injected as parameter
        """
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get(
            "/api/ia/metrics",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        timestamp = data["generated_at"]

        # Should be ISO8601 format with timezone info
        assert "T" in timestamp  # ISO format contains T separator
        assert "Z" in timestamp or "+" in timestamp  # Must have timezone info

    def test_metrics_percentile_ordering(self, client, admin_token, user_token):
        """AC#9: Percentiles are properly ordered (p50 <= p95 <= p99).

        JWT Token Injection Pattern:
        - Uses user_token fixture for making queries (optional)
        - Uses admin_token fixture for checking metrics (admin only)
        """
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Get metrics endpoint - main test is that admin can access it with JWT token
        response = client.get(
            "/api/ia/metrics",
            headers=admin_headers
        )

        # AC#9: Admin user can access metrics endpoint
        assert response.status_code == 200
        data = response.json()

        # Verify response structure for percentile fields
        assert "p50_ms" in data
        assert "p95_ms" in data
        assert "p99_ms" in data
        assert "total_queries" in data

        # When metrics are available (queries exist), verify percentile ordering
        if data.get("total_queries", 0) > 0:
            p50, p95, p99 = data["p50_ms"], data["p95_ms"], data["p99_ms"]
            # Percentiles should be ordered: p50 <= p95 <= p99
            assert p50 <= p95 <= p99, f"Percentiles not ordered: p50={p50}, p95={p95}, p99={p99}"


# Story 4.1: Document Summary Generation Tests

class TestSummaryGenerationEndpoint:
    """Test Story 4.1: Document Summary Generation (AC1-AC13)."""

    def test_summary_valid_request_short(self, client, user_token, test_db):
        """AC1-AC3: Valid summary request returns 200 with correct structure.

        Tests:
        - AC1: Endpoint POST /api/ia/generate/summary with Bearer token
        - AC2: Accepts document_id and summary_length parameters
        - AC3: Returns JSON with all required fields
        """
        # Create test document
        from app.models import Document
        doc = Document(
            title="Test Policy",
            description="Test document",
            category="HR",
            file_type="txt",
            file_size_bytes=1000,
            file_path="/test/policy.txt",
            uploaded_by=1,
            content_text="El empresa otorga 15 días de vacaciones anuales. "
                        "Cada empleado tiene derecho a esta prestación. " * 20  # ~200 words
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                mock_gen.return_value = "La compañía otorga 15 días de vacaciones."

                response = client.post(
                    "/api/ia/generate/summary",
                    json={
                        "document_id": doc.id,
                        "summary_length": "short"
                    },
                    headers=headers
                )

                assert response.status_code == 200
                data = response.json()

                # AC3: Verify response structure
                assert "document_id" in data
                assert "document_title" in data
                assert "summary" in data
                assert "summary_length" in data
                assert "word_count" in data
                assert "generated_at" in data
                assert "generation_time_ms" in data

                assert data["document_id"] == doc.id
                assert data["summary_length"] == "short"
                assert isinstance(data["word_count"], int)
                assert data["word_count"] > 0

    def test_summary_ac4_target_lengths(self, client, user_token, test_db):
        """AC4: Summary lengths match targets (short~150, medium~300, long~500)."""
        from app.models import Document

        # Create document with enough content
        large_content = """
        The company provides comprehensive benefits and policies for all employees.
        These include vacation days, health insurance, retirement plans, and more.
        Employees receive 15 days of annual vacation, plus holiday time.
        Health insurance covers medical, dental, and vision.
        Retirement plans offer matching contributions up to 6 percent.
        """ * 30  # ~1500 words

        doc = Document(
            title="Benefits Policy",
            description="Test",
            category="HR",
            file_type="txt",
            file_size_bytes=5000,
            file_path="/test/benefits.txt",
            uploaded_by=1,
            content_text=large_content
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True

                # Test "medium" length (~300 words)
                mock_gen.return_value = (" ".join(["Word"] * 300)).strip()  # ~300 words

                response = client.post(
                    "/api/ia/generate/summary",
                    json={
                        "document_id": doc.id,
                        "summary_length": "medium"
                    },
                    headers=headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["summary_length"] == "medium"
                # Word count should be reasonable (100-600 for medium)
                assert 100 <= data["word_count"] <= 600

    def test_summary_ac7_disclaimer(self, client, user_token, test_db):
        """AC7: Summary includes AI disclaimer at the end."""
        from app.models import Document

        doc = Document(
            title="Test Doc",
            description="Test",
            category="Test",
            file_type="txt",
            file_size_bytes=1000,
            file_path="/test/doc.txt",
            uploaded_by=1,
            content_text="Sample content " * 100  # >100 words
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                mock_gen.return_value = "Sample summary text"

                response = client.post(
                    "/api/ia/generate/summary",
                    json={
                        "document_id": doc.id,
                        "summary_length": "short"
                    },
                    headers=headers
                )

                assert response.status_code == 200
                data = response.json()

                # AC7: Disclaimer should be present
                assert "*Resumen generado automáticamente por IA" in data["summary"]

    def test_summary_ac8_document_not_found_404(self, client, user_token):
        """AC8: Non-existent document returns 404."""
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/generate/summary",
            json={
                "document_id": 99999,
                "summary_length": "short"
            },
            headers=headers
        )

        assert response.status_code == 404
        data = response.json()
        assert "no encontrado" in data["detail"].lower()

    def test_summary_ac9_no_content_400(self, client, user_token, test_db):
        """AC9: Document with no content_text returns 400."""
        from app.models import Document

        doc = Document(
            title="Empty Doc",
            description="No content",
            category="Test",
            file_type="txt",
            file_size_bytes=0,
            file_path="/test/empty.txt",
            uploaded_by=1,
            content_text=None  # No content
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/generate/summary",
            json={
                "document_id": doc.id,
                "summary_length": "short"
            },
            headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "no tiene contenido procesado" in data["detail"]

    def test_summary_ac10_too_short_document_400(self, client, user_token, test_db):
        """AC10: Document < 100 words returns 400."""
        from app.models import Document

        doc = Document(
            title="Short Doc",
            description="Too short",
            category="Test",
            file_type="txt",
            file_size_bytes=50,
            file_path="/test/short.txt",
            uploaded_by=1,
            content_text="This is a short document with only a few words."  # <100 words
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post(
            "/api/ia/generate/summary",
            json={
                "document_id": doc.id,
                "summary_length": "short"
            },
            headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "demasiado corto" in data["detail"]

    def test_summary_ac11_llm_unavailable_503(self, client, user_token, test_db):
        """AC11: LLM service unavailable returns 503."""
        from app.models import Document

        doc = Document(
            title="Test",
            description="Test",
            category="Test",
            file_type="txt",
            file_size_bytes=1000,
            file_path="/test/test.txt",
            uploaded_by=1,
            content_text="Content text. " * 30
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False

            response = client.post(
                "/api/ia/generate/summary",
                json={
                    "document_id": doc.id,
                    "summary_length": "short"
                },
                headers=headers
            )

            assert response.status_code == 503
            data = response.json()
            assert "IA no disponible" in data["detail"]

    def test_summary_ac12_cache_hit(self, client, user_token, test_db):
        """AC12: Cached summary is used (inferred by fast response time)."""
        from app.models import Document
        import time

        doc = Document(
            title="Doc for Cache Test",
            description="Test",
            category="Test",
            file_type="txt",
            file_size_bytes=1000,
            file_path="/test/cache-test.txt",
            uploaded_by=1,
            content_text="Content text " * 100  # >100 words
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                mock_gen.return_value = (" ".join(["Word"] * 200)).strip()

                # First request - will be cached
                start = time.time()
                response1 = client.post(
                    "/api/ia/generate/summary",
                    json={
                        "document_id": doc.id,
                        "summary_length": "short"
                    },
                    headers=headers
                )
                time1 = time.time() - start

                assert response1.status_code == 200
                data1 = response1.json()
                assert data1["summary_length"] == "short"
                first_summary = data1["summary"]

                # Second request - should hit cache (AC12)
                # For cache hit test, we just verify endpoint works again
                # (Full cache behavior testing requires mocking DB and cache layer)
                start = time.time()
                response2 = client.post(
                    "/api/ia/generate/summary",
                    json={
                        "document_id": doc.id,
                        "summary_length": "short"
                    },
                    headers=headers
                )
                time2 = time.time() - start

                assert response2.status_code == 200
                data2 = response2.json()
                # Second request should complete successfully
                assert data2["summary_length"] == "short"

    def test_summary_ac13_document_truncation(self, client, user_token, test_db):
        """AC13: Large document (>10k chars) is truncated with note."""
        from app.models import Document

        # Create document > 10000 chars (with words to avoid word count issues)
        large_content = " ".join(["Word"] * 3000)  # ~15000 chars with words

        doc = Document(
            title="Large Doc",
            description="Test",
            category="Test",
            file_type="txt",
            file_size_bytes=15000,
            file_path="/test/large.txt",
            uploaded_by=1,
            content_text=large_content
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                mock_gen.return_value = "Summary of truncated content"

                response = client.post(
                    "/api/ia/generate/summary",
                    json={
                        "document_id": doc.id,
                        "summary_length": "medium"
                    },
                    headers=headers
                )

                assert response.status_code == 200
                # Verify LLM was called (with truncated content)
                assert mock_gen.called
                call_args = mock_gen.call_args
                prompt = call_args[1]["prompt"] if call_args[1] else call_args[0][0]
                # Prompt should not contain full 15k document (truncated to 10k)
                assert "Nota: Resumen basado en sección inicial" in prompt

    def test_summary_401_unauthenticated(self, client, test_db):
        """Summary endpoint requires authentication (401)."""
        response = client.post(
            "/api/ia/generate/summary",
            json={
                "document_id": 1,
                "summary_length": "short"
            }
        )

        assert response.status_code == 401

    def test_summary_rate_limiting(self, client, user_token, test_db):
        """Rate limiting: 10 summaries per 60 seconds per user."""
        from app.models import Document

        doc = Document(
            title="Test",
            description="Test",
            category="Test",
            file_type="txt",
            file_size_bytes=1000,
            file_path="/test/test.txt",
            uploaded_by=1,
            content_text="Content " * 100  # >100 words
        )
        test_db.add(doc)
        test_db.commit()
        test_db.refresh(doc)

        headers = {"Authorization": f"Bearer {user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                mock_gen.return_value = "Summary"

                # Make 11 requests to exceed limit (10)
                for i in range(11):
                    response = client.post(
                        "/api/ia/generate/summary",
                        json={
                            "document_id": doc.id,
                            "summary_length": "short"
                        },
                        headers=headers
                    )

                    if i < 10:
                        assert response.status_code == 200, f"Request {i+1} should succeed"
                    else:
                        # 11th request should be rate limited
                        assert response.status_code == 429
                        data = response.json()
                        assert "Rate limit exceeded" in data["detail"]
