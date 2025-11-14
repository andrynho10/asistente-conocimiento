"""
Custom exception classes for IA service (Task 11).

AC#11: Error Handling and Validation
- QueryValidationError: Invalid query length or context mode
- OllamaUnavailableError: Ollama service unavailable
- RateLimitError: Rate limit exceeded
- LLMGenerationError: LLM generation failure (timeout, error)
- DatabaseError: Database operation failure

All exceptions are handled in main.py exception handlers
to return appropriate HTTP responses.
"""

from typing import Optional


class IAServiceException(Exception):
    """
    Base exception for IA service errors.

    AC#10: Service gracefully handles errors and logs appropriately.
    """
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        detail: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.http_status_code = http_status_code
        self.detail = detail or message
        super().__init__(self.message)


class QueryValidationError(IAServiceException):
    """
    AC#10: Malformed requests return clear error messages.
    AC#2: Query validation (length 10-500, context_mode enum).

    Raised when:
    - Query is shorter than 10 characters
    - Query is longer than 500 characters
    - context_mode is not "general" or "specific"
    """
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="QUERY_VALIDATION_ERROR",
            http_status_code=400,
            detail=detail or message
        )


class OllamaUnavailableError(IAServiceException):
    """
    AC#10: Service gracefully handles Ollama unavailability.
    AC#1: Returns 503 when Ollama service unavailable.

    Raised when:
    - Ollama service is not responding
    - Model is not available
    - Connection timeout to Ollama
    """
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="OLLAMA_UNAVAILABLE",
            http_status_code=503,
            detail=detail or "AI service is currently unavailable. Please try again later."
        )


class RateLimitError(IAServiceException):
    """
    AC#6: Rate limiting enforcement (10 queries per 60 seconds per user).

    Raised when:
    - User exceeds rate limit
    """
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            http_status_code=429,
            detail=detail or "Rate limit exceeded: 10 queries per 60 seconds per user"
        )


class LLMGenerationError(IAServiceException):
    """
    AC#10: Network timeouts from Ollama handled with 503.
    AC#4: LLM generation failure handling.

    Raised when:
    - LLM generation times out
    - LLM returns invalid/empty response
    - LLM internal error
    """
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="LLM_GENERATION_FAILED",
            http_status_code=503,
            detail=detail or "AI response generation failed. Please try again later."
        )


class DatabaseError(IAServiceException):
    """
    AC#10: Database errors logged and user receives generic message.

    Raised when:
    - Query/PerformanceMetric model persistence fails
    - Audit logging fails
    - Metrics calculation fails
    """
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            http_status_code=500,
            detail=detail or "An error occurred while processing your request"
        )


class RetrievalServiceError(IAServiceException):
    """
    AC#3: Retrieval service integration errors.

    Raised when:
    - Document search fails
    - FTS5 query fails
    - No documents found (gracefully handled)
    """
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="RETRIEVAL_FAILED",
            http_status_code=500,
            detail=detail or "Failed to retrieve documents"
        )


class RetrievalTimeoutError(IAServiceException):
    """
    AC#11: Retrieval service timeout handling.

    Raised when:
    - Document search exceeds timeout threshold
    - FTS5 query execution timeout
    """
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="RETRIEVAL_TIMEOUT",
            http_status_code=503,
            detail=detail or "Document search timed out. Please try a simpler query."
        )


class DatabaseTimeoutError(IAServiceException):
    """
    AC#11: Database operation timeout handling.

    Raised when:
    - Database query exceeds timeout threshold
    - Database operation takes too long
    """
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_TIMEOUT",
            http_status_code=503,
            detail=detail or "Database operation timed out. Please try again later."
        )
