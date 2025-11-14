"""
Unit tests for IA schemas validation.

Tests schema validation for QueryRequest, QueryResponse, SourceInfo,
HealthResponse, and ErrorResponse models.

AC#1, AC#2, AC#5: Schema validation for IA API endpoints.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.ia import (
    QueryRequest,
    QueryResponse,
    SourceInfo,
    HealthResponse,
    ErrorResponse,
)


class TestQueryRequestSchema:
    """Test QueryRequest schema validation (AC#2)."""

    def test_valid_query_request(self):
        """Valid QueryRequest with required fields."""
        request = QueryRequest(
            query="¿Cuál es la política de vacaciones?",
            context_mode="general"
        )
        assert request.query == "¿Cuál es la política de vacaciones?"
        assert request.context_mode == "general"
        assert request.temperature == 0.7
        assert request.max_tokens == 500
        assert request.top_k == 3

    def test_query_request_with_all_fields(self):
        """QueryRequest with all optional fields specified."""
        request = QueryRequest(
            query="Información sobre procedimientos de contratación",
            context_mode="specific",
            top_k=5,
            temperature=0.5,
            max_tokens=1000
        )
        assert request.query == "Información sobre procedimientos de contratación"
        assert request.context_mode == "specific"
        assert request.top_k == 5
        assert request.temperature == 0.5
        assert request.max_tokens == 1000

    def test_query_too_short(self):
        """AC#2: Query must be at least 10 characters."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query="short")
        errors = exc_info.value.errors()
        assert any("at least 10 characters" in str(e) for e in errors)

    def test_query_too_long(self):
        """AC#2: Query must not exceed 500 characters."""
        long_query = "a" * 501
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query=long_query)
        errors = exc_info.value.errors()
        assert any("at most 500 characters" in str(e) for e in errors)

    def test_query_empty(self):
        """AC#2: Query cannot be empty or whitespace only."""
        with pytest.raises(ValidationError):
            QueryRequest(query="")

    def test_query_whitespace_only(self):
        """AC#2: Query cannot be whitespace only."""
        with pytest.raises(ValidationError):
            QueryRequest(query="   ")

    def test_invalid_context_mode(self):
        """AC#2: context_mode must be 'general' or 'specific'."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                query="Válida pregunta de prueba aquí",
                context_mode="invalid"
            )
        errors = exc_info.value.errors()
        assert any("pattern" in str(e) for e in errors)

    def test_context_mode_general(self):
        """AC#2: context_mode 'general' is valid."""
        request = QueryRequest(
            query="Pregunta válida para el sistema",
            context_mode="general"
        )
        assert request.context_mode == "general"

    def test_context_mode_specific(self):
        """AC#2: context_mode 'specific' is valid."""
        request = QueryRequest(
            query="Pregunta válida para el sistema",
            context_mode="specific"
        )
        assert request.context_mode == "specific"

    def test_temperature_boundary_min(self):
        """AC#4: Temperature must be between 0.0 and 1.0."""
        request = QueryRequest(
            query="Pregunta válida para el sistema",
            temperature=0.0
        )
        assert request.temperature == 0.0

    def test_temperature_boundary_max(self):
        """AC#4: Temperature must be between 0.0 and 1.0."""
        request = QueryRequest(
            query="Pregunta válida para el sistema",
            temperature=1.0
        )
        assert request.temperature == 1.0

    def test_temperature_out_of_bounds_low(self):
        """AC#4: Temperature below 0.0 is invalid."""
        with pytest.raises(ValidationError):
            QueryRequest(
                query="Pregunta válida para el sistema",
                temperature=-0.1
            )

    def test_temperature_out_of_bounds_high(self):
        """AC#4: Temperature above 1.0 is invalid."""
        with pytest.raises(ValidationError):
            QueryRequest(
                query="Pregunta válida para el sistema",
                temperature=1.1
            )

    def test_max_tokens_validation(self):
        """AC#4: max_tokens must be between 1 and 4096."""
        request = QueryRequest(
            query="Pregunta válida para el sistema",
            max_tokens=500
        )
        assert request.max_tokens == 500

    def test_max_tokens_min_boundary(self):
        """AC#4: max_tokens minimum is 1."""
        request = QueryRequest(
            query="Pregunta válida para el sistema",
            max_tokens=1
        )
        assert request.max_tokens == 1

    def test_max_tokens_max_boundary(self):
        """AC#4: max_tokens maximum is 4096."""
        request = QueryRequest(
            query="Pregunta válida para el sistema",
            max_tokens=4096
        )
        assert request.max_tokens == 4096

    def test_max_tokens_out_of_bounds(self):
        """AC#4: max_tokens > 4096 is invalid."""
        with pytest.raises(ValidationError):
            QueryRequest(
                query="Pregunta válida para el sistema",
                max_tokens=4097
            )

    def test_top_k_validation(self):
        """AC#3: top_k must be between 1 and 10."""
        request = QueryRequest(
            query="Pregunta válida para el sistema",
            top_k=3
        )
        assert request.top_k == 3

    def test_query_stripped(self):
        """Query should be stripped of leading/trailing whitespace."""
        request = QueryRequest(query="  Pregunta válida para el sistema  ")
        assert request.query == "Pregunta válida para el sistema"


class TestSourceInfoSchema:
    """Test SourceInfo schema validation (AC#5)."""

    def test_valid_source_info(self):
        """Valid SourceInfo with all required fields."""
        source = SourceInfo(
            document_id=1,
            title="Política de Vacaciones Anuales",
            relevance_score=0.95
        )
        assert source.document_id == 1
        assert source.title == "Política de Vacaciones Anuales"
        assert source.relevance_score == 0.95

    def test_source_info_relevance_score_min(self):
        """AC#5: Relevance score must be between 0.0 and 1.0."""
        source = SourceInfo(
            document_id=1,
            title="Documento",
            relevance_score=0.0
        )
        assert source.relevance_score == 0.0

    def test_source_info_relevance_score_max(self):
        """AC#5: Relevance score must be between 0.0 and 1.0."""
        source = SourceInfo(
            document_id=42,
            title="Documento",
            relevance_score=1.0
        )
        assert source.relevance_score == 1.0

    def test_source_info_relevance_score_normalized(self):
        """AC#5: Relevance score is normalized to 0.0-1.0."""
        source = SourceInfo(
            document_id=10,
            title="Documento",
            relevance_score=0.72
        )
        assert 0.0 <= source.relevance_score <= 1.0
        assert source.relevance_score == 0.72

    def test_source_info_invalid_score_below(self):
        """AC#5: Relevance score below 0.0 is invalid."""
        with pytest.raises(ValidationError):
            SourceInfo(
                document_id=1,
                title="Documento",
                relevance_score=-0.1
            )

    def test_source_info_invalid_score_above(self):
        """AC#5: Relevance score above 1.0 is invalid."""
        with pytest.raises(ValidationError):
            SourceInfo(
                document_id=1,
                title="Documento",
                relevance_score=1.1
            )


class TestQueryResponseSchema:
    """Test QueryResponse schema validation (AC#5)."""

    def test_valid_query_response(self):
        """Valid QueryResponse with all required fields."""
        response = QueryResponse(
            query="¿Cuál es la política de vacaciones?",
            answer="Los empleados tienen derecho a 15 días hábiles de vacaciones anuales.",
            sources=[
                SourceInfo(
                    document_id=1,
                    title="Política de Vacaciones Anuales",
                    relevance_score=0.95
                )
            ],
            response_time_ms=1245.5,
            documents_retrieved=1
        )
        assert response.query == "¿Cuál es la política de vacaciones?"
        assert len(response.sources) == 1
        assert response.response_time_ms == 1245.5
        assert response.documents_retrieved == 1

    def test_query_response_empty_sources(self):
        """AC#3: QueryResponse handles empty result set gracefully."""
        response = QueryResponse(
            query="Pregunta con sin resultados",
            answer="No encontré documentos relevantes para tu consulta.",
            sources=[],
            response_time_ms=120.3,
            documents_retrieved=0
        )
        assert len(response.sources) == 0
        assert response.documents_retrieved == 0

    def test_query_response_timestamp_default(self):
        """AC#5: timestamp uses ISO format with default to current time."""
        from datetime import timezone
        response = QueryResponse(
            query="Pregunta válida",
            answer="Respuesta válida",
            sources=[],
            response_time_ms=100.0,
            documents_retrieved=0
        )
        assert isinstance(response.timestamp, datetime)
        # Should be close to now (within 1 second)
        time_diff = abs((datetime.now(timezone.utc) - response.timestamp).total_seconds())
        assert time_diff < 1.0

    def test_query_response_custom_timestamp(self):
        """AC#5: timestamp can be set explicitly."""
        custom_time = datetime(2025, 11, 13, 10, 30, 0)
        response = QueryResponse(
            query="Pregunta válida",
            answer="Respuesta válida",
            sources=[],
            response_time_ms=100.0,
            documents_retrieved=0,
            timestamp=custom_time
        )
        assert response.timestamp == custom_time

    def test_query_response_response_time_negative(self):
        """AC#5: response_time_ms must be >= 0."""
        with pytest.raises(ValidationError):
            QueryResponse(
                query="Pregunta válida",
                answer="Respuesta válida",
                sources=[],
                response_time_ms=-100.0,
                documents_retrieved=0
            )

    def test_query_response_documents_count_matches_sources(self):
        """AC#5: documents_retrieved count should match sources list length."""
        sources = [
            SourceInfo(document_id=i+1, title=f"Doc {i+1}", relevance_score=0.9)
            for i in range(3)
        ]
        response = QueryResponse(
            query="Pregunta válida",
            answer="Respuesta válida",
            sources=sources,
            response_time_ms=1500.0,
            documents_retrieved=3
        )
        assert response.documents_retrieved == len(response.sources)

    def test_query_response_multiple_sources(self):
        """AC#5: QueryResponse can contain multiple sources."""
        sources = [
            SourceInfo(
                document_id=1,
                title="Documento 1",
                relevance_score=0.95
            ),
            SourceInfo(
                document_id=2,
                title="Documento 2",
                relevance_score=0.87
            ),
            SourceInfo(
                document_id=3,
                title="Documento 3",
                relevance_score=0.72
            )
        ]
        response = QueryResponse(
            query="Pregunta válida",
            answer="Respuesta con múltiples fuentes",
            sources=sources,
            response_time_ms=2000.0,
            documents_retrieved=3
        )
        assert len(response.sources) == 3
        assert response.documents_retrieved == 3


class TestHealthResponseSchema:
    """Test HealthResponse schema validation (AC#1)."""

    def test_valid_health_response_ok(self):
        """Valid HealthResponse with status 'ok'."""
        response = HealthResponse(
            status="ok",
            model="llama3.1:8b-instruct-q4_K_M",
            ollama_version="0.1.20"
        )
        assert response.status == "ok"
        assert response.model == "llama3.1:8b-instruct-q4_K_M"

    def test_valid_health_response_unavailable(self):
        """Valid HealthResponse with status 'unavailable'."""
        response = HealthResponse(
            status="unavailable",
            error="Connection refused"
        )
        assert response.status == "unavailable"
        assert response.error == "Connection refused"

    def test_health_response_invalid_status(self):
        """AC#1: Status must be 'ok' or 'unavailable'."""
        with pytest.raises(ValidationError) as exc_info:
            HealthResponse(status="unknown")
        errors = exc_info.value.errors()
        assert any("pattern" in str(e) for e in errors)

    def test_health_response_response_time_non_negative(self):
        """AC#1: response_time_ms must be >= 0."""
        with pytest.raises(ValidationError):
            HealthResponse(
                status="ok",
                response_time_ms=-1.0
            )


class TestErrorResponseSchema:
    """Test ErrorResponse schema validation (AC#10)."""

    def test_valid_error_response(self):
        """Valid ErrorResponse with required fields."""
        response = ErrorResponse(
            error="Service unavailable",
            code="SERVICE_UNAVAILABLE"
        )
        assert response.error == "Service unavailable"
        assert response.code == "SERVICE_UNAVAILABLE"

    def test_error_response_with_detail(self):
        """ErrorResponse with optional detail field."""
        response = ErrorResponse(
            error="Invalid request",
            detail="Query length must be between 10 and 500 characters",
            code="INVALID_QUERY"
        )
        assert response.error == "Invalid request"
        assert response.detail == "Query length must be between 10 and 500 characters"

    def test_error_response_timestamp_default(self):
        """AC#10: Error timestamp defaults to current time."""
        response = ErrorResponse(error="Test error")
        assert isinstance(response.timestamp, datetime)

    def test_error_response_custom_timestamp(self):
        """AC#10: Error timestamp can be set explicitly."""
        custom_time = datetime(2025, 11, 13, 10, 30, 0)
        response = ErrorResponse(
            error="Test error",
            timestamp=custom_time
        )
        assert response.timestamp == custom_time
