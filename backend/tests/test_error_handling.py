"""
Test error handling and custom exceptions (Task 11).

AC#11: Error Handling and Validation
- QueryValidationError: Invalid query length or context mode
- OllamaUnavailableError: Ollama service unavailable
- RateLimitError: Rate limit exceeded
- LLMGenerationError: LLM generation failure
- DatabaseError: Database operation failure

AC#10: Error Handling and Resilience
- Service gracefully handles errors
- No stack traces or internal details exposed
- Clear error messages with error codes
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.exceptions import (
    QueryValidationError,
    OllamaUnavailableError,
    RateLimitError,
    LLMGenerationError,
    DatabaseError,
    RetrievalServiceError
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestQueryValidationError:
    """Test QueryValidationError exception."""

    def test_exception_creation(self):
        """Test QueryValidationError can be created."""
        error = QueryValidationError("Query too short")

        assert error.error_code == "QUERY_VALIDATION_ERROR"
        assert error.http_status_code == 400
        assert "Query too short" in error.message

    def test_exception_with_detail(self):
        """Test QueryValidationError with custom detail."""
        error = QueryValidationError(
            "Query invalid",
            detail="Query must be between 10 and 500 characters"
        )

        assert error.detail == "Query must be between 10 and 500 characters"
        assert error.http_status_code == 400

    def test_exception_is_string_representable(self):
        """Test exception can be converted to string."""
        error = QueryValidationError("Query is invalid")
        assert "Query is invalid" in str(error)


class TestOllamaUnavailableError:
    """Test OllamaUnavailableError exception."""

    def test_exception_creation(self):
        """Test OllamaUnavailableError can be created."""
        error = OllamaUnavailableError("Ollama service not responding")

        assert error.error_code == "OLLAMA_UNAVAILABLE"
        assert error.http_status_code == 503

    def test_exception_default_detail(self):
        """Test OllamaUnavailableError default detail message."""
        error = OllamaUnavailableError("Connection failed")

        # Should have a generic user-friendly message
        assert "AI service is currently unavailable" in error.detail

    def test_exception_with_custom_detail(self):
        """Test OllamaUnavailableError with custom detail."""
        error = OllamaUnavailableError(
            "Timeout",
            detail="Request timed out after 10 seconds"
        )

        assert error.detail == "Request timed out after 10 seconds"


class TestRateLimitError:
    """Test RateLimitError exception."""

    def test_exception_creation(self):
        """Test RateLimitError can be created."""
        error = RateLimitError("Rate limit exceeded for user 123")

        assert error.error_code == "RATE_LIMIT_EXCEEDED"
        assert error.http_status_code == 429

    def test_exception_detail_message(self):
        """Test RateLimitError has rate limit details."""
        error = RateLimitError("Too many requests")

        # Should mention the rate limit policy
        assert "10 queries per 60 seconds" in error.detail


class TestLLMGenerationError:
    """Test LLMGenerationError exception."""

    def test_exception_creation(self):
        """Test LLMGenerationError can be created."""
        error = LLMGenerationError("Generation timeout")

        assert error.error_code == "LLM_GENERATION_FAILED"
        assert error.http_status_code == 503

    def test_exception_generic_detail(self):
        """Test LLMGenerationError provides generic detail to user."""
        error = LLMGenerationError("Internal error: X happened")

        # Should have generic message for user, not expose internal error
        assert "AI response generation failed" in error.detail
        assert "Internal error" not in error.detail


class TestDatabaseError:
    """Test DatabaseError exception."""

    def test_exception_creation(self):
        """Test DatabaseError can be created."""
        error = DatabaseError("Failed to insert query record")

        assert error.error_code == "DATABASE_ERROR"
        assert error.http_status_code == 500

    def test_exception_generic_detail_for_user(self):
        """Test DatabaseError provides generic message to user."""
        error = DatabaseError("Connection pool exhausted: PGPOOL_ERROR_001")

        # Should not expose database details to user
        assert "processing your request" in error.detail
        assert "Connection pool" not in error.detail


class TestRetrievalServiceError:
    """Test RetrievalServiceError exception."""

    def test_exception_creation(self):
        """Test RetrievalServiceError can be created."""
        error = RetrievalServiceError("FTS5 query failed")

        assert error.error_code == "RETRIEVAL_FAILED"
        assert error.http_status_code == 500


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """All custom exceptions should inherit from IAServiceException."""
        from app.exceptions import IAServiceException

        exceptions = [
            QueryValidationError("test"),
            OllamaUnavailableError("test"),
            RateLimitError("test"),
            LLMGenerationError("test"),
            DatabaseError("test"),
            RetrievalServiceError("test")
        ]

        for exc in exceptions:
            assert isinstance(exc, IAServiceException)

    def test_exception_attributes(self):
        """Test exception attributes are properly set."""
        error = QueryValidationError("Test message")

        assert hasattr(error, 'message')
        assert hasattr(error, 'error_code')
        assert hasattr(error, 'http_status_code')
        assert hasattr(error, 'detail')


class TestExceptionErrorCodes:
    """Test exception error codes for programmatic handling."""

    def test_unique_error_codes(self):
        """Each exception type should have a unique error code."""
        exceptions = [
            QueryValidationError("test"),
            OllamaUnavailableError("test"),
            RateLimitError("test"),
            LLMGenerationError("test"),
            DatabaseError("test"),
            RetrievalServiceError("test")
        ]

        codes = [exc.error_code for exc in exceptions]
        # All codes should be unique
        assert len(codes) == len(set(codes))

    def test_error_codes_are_screaming_snake_case(self):
        """Error codes should be SCREAMING_SNAKE_CASE."""
        exceptions = [
            QueryValidationError("test"),
            OllamaUnavailableError("test"),
            RateLimitError("test"),
            LLMGenerationError("test"),
            DatabaseError("test"),
            RetrievalServiceError("test")
        ]

        for exc in exceptions:
            # Should be uppercase with underscores
            assert exc.error_code == exc.error_code.upper()
            assert '_' in exc.error_code or len(exc.error_code) == 1


class TestExceptionHTTPStatusCodes:
    """Test HTTP status codes for exceptions."""

    def test_validation_error_is_400(self):
        """QueryValidationError should return 400."""
        error = QueryValidationError("test")
        assert error.http_status_code == 400

    def test_ollama_unavailable_is_503(self):
        """OllamaUnavailableError should return 503."""
        error = OllamaUnavailableError("test")
        assert error.http_status_code == 503

    def test_rate_limit_error_is_429(self):
        """RateLimitError should return 429."""
        error = RateLimitError("test")
        assert error.http_status_code == 429

    def test_llm_generation_error_is_503(self):
        """LLMGenerationError should return 503."""
        error = LLMGenerationError("test")
        assert error.http_status_code == 503

    def test_database_error_is_500(self):
        """DatabaseError should return 500."""
        error = DatabaseError("test")
        assert error.http_status_code == 500

    def test_retrieval_error_is_500(self):
        """RetrievalServiceError should return 500."""
        error = RetrievalServiceError("test")
        assert error.http_status_code == 500


class TestExceptionDetailMessages:
    """Test exception detail messages for users."""

    def test_no_internal_details_exposed(self):
        """Exception details should not expose internal implementation."""
        # Simulate internal database error
        error = DatabaseError(
            "PostgreSQL error: UNIQUE constraint violated on users.email",
            detail="Email already exists in the system"
        )

        # User-facing detail should be generic
        assert "PostgreSQL" not in error.detail
        assert "constraint" not in error.detail.lower()

    def test_all_exceptions_have_user_friendly_details(self):
        """All exceptions should have user-friendly detail messages."""
        exceptions = [
            QueryValidationError("Internal validation failed"),
            OllamaUnavailableError("Connection refused"),
            RateLimitError("Rate limit exceeded for user 123"),
            LLMGenerationError("Generation timeout"),
            DatabaseError("Database connection failed"),
            RetrievalServiceError("Index corruption")
        ]

        for exc in exceptions:
            # Detail should be present and not empty
            assert exc.detail
            assert len(exc.detail) > 0
            # Should be a string
            assert isinstance(exc.detail, str)
