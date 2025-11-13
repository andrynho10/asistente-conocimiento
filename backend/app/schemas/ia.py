"""
IA (Inteligencia Artificial) Schemas

Pydantic models for AI/LLM related API responses and requests.
Provides structured data contracts for IA endpoints with validation
and OpenAPI documentation support.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class HealthResponse(BaseModel):
    """
    Response model for IA service health check endpoint.

    Provides information about Ollama service availability,
    model status, and version information.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "model": "llama3.1:8b-instruct-q4_K_M",
                    "ollama_version": "0.1.20",
                    "available_at": "2025-11-13T10:30:00Z",
                    "response_time_ms": 125.5
                },
                {
                    "status": "unavailable",
                    "error": "Connection refused",
                    "available_at": "2025-11-13T10:30:00Z",
                    "response_time_ms": 1000.0
                }
            ]
        }
    )

    status: str = Field(
        ...,
        description="Service status",
        pattern="^(ok|unavailable)$",
        examples=["ok", "unavailable"]
    )
    model: Optional[str] = Field(
        None,
        description="Currently configured LLM model",
        examples=["llama3.1:8b-instruct-q4_K_M"]
    )
    ollama_version: Optional[str] = Field(
        None,
        description="Ollama server version",
        examples=["0.1.20"]
    )
    available_at: Optional[datetime] = Field(
        None,
        description="Timestamp when availability was checked"
    )
    response_time_ms: Optional[float] = Field(
        None,
        description="Health check response time in milliseconds",
        ge=0,
        examples=[125.5]
    )
    error: Optional[str] = Field(
        None,
        description="Error message if service is unavailable",
        examples=["Connection refused", "Request timeout"]
    )


class GenerationRequest(BaseModel):
    """
    Request model for text generation endpoint.

    Defines parameters for LLM text generation with validation
    and reasonable defaults.
    """
    prompt: str = Field(
        ...,
        description="Input prompt for text generation",
        min_length=1,
        max_length=10000,
        examples=["¿Qué es el aprendizaje automático?"]
    )
    temperature: Optional[float] = Field(
        0.3,
        description="Sampling temperature (0.0-1.0, lower = more deterministic)",
        ge=0.0,
        le=1.0,
        examples=[0.3, 0.7, 1.0]
    )
    max_tokens: Optional[int] = Field(
        500,
        description="Maximum number of tokens to generate",
        ge=1,
        le=4096,
        examples=[100, 500, 1000]
    )
    stream: Optional[bool] = Field(
        False,
        description="Whether to stream the response (not implemented yet)",
        examples=[False]
    )

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        """Validate prompt content."""
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty or whitespace only')
        return v.strip()


class GenerationResponse(BaseModel):
    """
    Response model for text generation endpoint.

    Contains the generated text along with metadata about
    the generation process.
    """
    response: str = Field(
        ...,
        description="Generated text response",
        examples=["El aprendizaje automático es una rama de la inteligencia artificial..."]
    )
    model: str = Field(
        ...,
        description="Model used for generation",
        examples=["llama3.1:8b-instruct-q4_K_M"]
    )
    prompt_tokens: Optional[int] = Field(
        None,
        description="Number of tokens in the input prompt",
        ge=0,
        examples=[25]
    )
    response_tokens: Optional[int] = Field(
        None,
        description="Number of tokens in the generated response",
        ge=0,
        examples=[150]
    )
    total_tokens: Optional[int] = Field(
        None,
        description="Total tokens processed (prompt + response)",
        ge=0,
        examples=[175]
    )
    generation_time_ms: Optional[float] = Field(
        None,
        description="Time taken to generate response in milliseconds",
        ge=0,
        examples=[2500.0]
    )
    temperature: float = Field(
        ...,
        description="Temperature used for generation",
        ge=0.0,
        le=1.0,
        examples=[0.3]
    )


class ModelInfo(BaseModel):
    """
    Model information response.

    Provides detailed information about available models
    and their capabilities.
    """
    name: str = Field(
        ...,
        description="Model name",
        examples=["llama3.1:8b-instruct-q4_K_M"]
    )
    size: Optional[int] = Field(
        None,
        description="Model size in bytes",
        ge=0,
        examples=[5033164800]  # ~4.7GB
    )
    digest: Optional[str] = Field(
        None,
        description="Model digest/hash",
        examples=["sha256:abc123..."]
    )
    modified_at: Optional[datetime] = Field(
        None,
        description="Last modification timestamp"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional model details"
    )


class ModelListResponse(BaseModel):
    """
    Response model for listing available models.

    Contains a list of all available models with their
    respective information.
    """
    models: List[ModelInfo] = Field(
        ...,
        description="List of available models",
        examples=[[
            {
                "name": "llama3.1:8b-instruct-q4_K_M",
                "size": 5033164800,
                "digest": "sha256:abc123...",
                "modified_at": "2025-11-13T10:30:00Z"
            }
        ]]
    )
    total: int = Field(
        ...,
        description="Total number of available models",
        ge=0,
        examples=[1, 3, 5]
    )


class ErrorResponse(BaseModel):
    """
    Standard error response model for IA endpoints.

    Provides consistent error format across all IA endpoints
    with appropriate HTTP status codes.
    """
    error: str = Field(
        ...,
        description="Error message",
        examples=["Service unavailable", "Invalid request", "Internal server error"]
    )
    detail: Optional[str] = Field(
        None,
        description="Detailed error information",
        examples=["Ollama service is not responding at localhost:11434"]
    )
    code: Optional[str] = Field(
        None,
        description="Error code for programmatic handling",
        examples=["SERVICE_UNAVAILABLE", "INVALID_PROMPT", "TIMEOUT"]
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )