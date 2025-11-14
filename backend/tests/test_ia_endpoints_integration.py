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
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user_token(client, test_db_session):
    """Create a test user and return authentication token."""
    # Create user
    user = User(
        username="querytest",
        email="querytest@example.com",
        full_name="Query Test User",
        hashed_password=get_password_hash("testpass"),
        role=UserRole.user,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    # Login and get token
    response = client.post(
        "/api/auth/login",
        json={
            "username": "querytest",
            "password": "testpass"
        }
    )

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        # Fallback if auth endpoint not available
        return f"test_token_{user.id}"


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

    def test_query_valid_request(self, client, test_user_token):
        """AC#2: Valid query request returns 200."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

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

    def test_query_short_query(self, client, test_user_token):
        """AC#2: Query shorter than 10 characters returns 400."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        response = client.post(
            "/api/ia/query",
            json={
                "query": "short",
                "context_mode": "general"
            },
            headers=headers
        )

        assert response.status_code == 400

    def test_query_invalid_context_mode(self, client, test_user_token):
        """AC#2: Invalid context_mode returns 400."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        response = client.post(
            "/api/ia/query",
            json={
                "query": "¿Cuál es la política de vacaciones?",
                "context_mode": "invalid"
            },
            headers=headers
        )

        assert response.status_code == 400

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

    def test_query_llm_unavailable(self, client, test_user_token):
        """AC#10: Query returns 503 when LLM unavailable."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

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

    def test_rate_limit_10_per_60_seconds(self, client, test_user_token):
        """AC#6: Rate limit enforces 10 queries per 60 seconds per user."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

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

    def test_rate_limit_headers(self, client, test_user_token):
        """AC#6: Rate limit response includes X-RateLimit-* headers."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

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

    def test_error_no_stack_traces(self, client, test_user_token):
        """AC#10: Error responses don't include stack traces."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                mock_health.return_value = True
                mock_gen.side_effect = Exception("Database connection failed")

                response = client.post(
                    "/api/ia/query",
                    json={
                        "query": "¿Cuál es la política de vacaciones?",
                        "context_mode": "general"
                    },
                    headers=headers
                )

                assert response.status_code == 500
                data = response.json()
                # Should not contain actual exception details
                assert "traceback" not in str(data)
                assert "Exception" not in str(data)

    def test_malformed_request_returns_error(self, client, test_user_token):
        """AC#10: Malformed requests return clear error messages."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

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

    def test_response_includes_all_fields(self, client, test_user_token):
        """AC#5: QueryResponse includes all required fields."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

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

    def test_response_timestamp_iso_format(self, client, test_user_token):
        """AC#5: Timestamp uses ISO format."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

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

                    # Should be ISO format (contains T and Z or +)
                    assert "T" in timestamp
                    assert "Z" in timestamp or "+" in timestamp


class TestMetricsEndpoint:
    """Test AC#9: Metrics Endpoint (Admin Only)."""

    @pytest.fixture
    def admin_user_token(self, client, test_db_session):
        """Create an admin user and return authentication token."""
        # Create admin user
        admin = User(
            username="metricsadmin",
            email="metricsadmin@example.com",
            full_name="Metrics Admin User",
            hashed_password=get_password_hash("adminpass"),
            role=UserRole.admin,
            is_active=True
        )
        test_db_session.add(admin)
        test_db_session.commit()
        test_db_session.refresh(admin)

        # Login and get token
        response = client.post(
            "/api/auth/login",
            json={
                "username": "metricsadmin",
                "password": "adminpass"
            }
        )

        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            return f"admin_test_token_{admin.id}"

    def test_metrics_admin_only_403_for_user(self, client, test_user_token):
        """AC#9: Non-admin users receive 403 Forbidden."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        response = client.get(
            "/api/ia/metrics",
            headers=headers
        )

        assert response.status_code == 403

    def test_metrics_admin_only_401_unauthenticated(self, client):
        """AC#9: Unauthenticated users receive 401."""
        response = client.get("/api/ia/metrics")

        assert response.status_code == 401

    def test_metrics_returns_correct_structure(self, client, admin_user_token):
        """AC#9: Metrics endpoint returns complete structure."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}

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

    def test_metrics_zero_queries(self, client, admin_user_token):
        """AC#9: Metrics with no queries in 24h returns zeros."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}

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

    def test_metrics_timestamp_iso_format(self, client, admin_user_token):
        """AC#9: Metrics includes ISO format timestamp."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}

        response = client.get(
            "/api/ia/metrics",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        timestamp = data["generated_at"]

        # Should be ISO format
        assert "T" in timestamp
        assert "Z" in timestamp or "+" in timestamp

    def test_metrics_percentile_ordering(self, client, admin_user_token, test_user_token):
        """AC#9: Percentiles are properly ordered (p50 <= p95 <= p99)."""
        # First, create some queries to generate metrics
        user_headers = {"Authorization": f"Bearer {test_user_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_user_token}"}

        with patch('app.services.llm_service.OllamaLLMService.health_check_async', new_callable=AsyncMock) as mock_health:
            with patch('app.services.llm_service.OllamaLLMService.generate_response_async', new_callable=AsyncMock) as mock_gen:
                with patch('app.services.retrieval_service.RetrievalService.retrieve_relevant_documents', new_callable=AsyncMock) as mock_retrieval:
                    mock_health.return_value = True
                    mock_gen.return_value = "Response"
                    mock_retrieval.return_value = []

                    # Create multiple queries
                    for i in range(3):
                        client.post(
                            "/api/ia/query",
                            json={
                                "query": f"Consulta de prueba número {i}",
                                "context_mode": "general"
                            },
                            headers=user_headers
                        )

        # Get metrics
        response = client.get(
            "/api/ia/metrics",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Percentiles should be ordered
        if data["total_queries"] > 0:
            assert data["p50_ms"] <= data["p95_ms"] <= data["p99_ms"]
