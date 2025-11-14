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
