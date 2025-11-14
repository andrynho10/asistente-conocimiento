"""
IA (Inteligencia Artificial) Schemas

Pydantic models for AI/LLM related API responses and requests.
Provides structured data contracts for IA endpoints with validation
and OpenAPI documentation support.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class HealthResponse(BaseModel):
    """
    Response model for IA service health check endpoint.

    Provides information about Ollama service availability,
    model status, and version information.

    Task 10 Addition:
    - Includes cache_stats with cache performance metrics (AC#2)
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "model": "llama3.1:8b-instruct-q4_K_M",
                    "ollama_version": "0.1.20",
                    "available_at": "2025-11-13T10:30:00Z",
                    "response_time_ms": 125.5,
                    "cache_stats": {
                        "cache_size": 45,
                        "hit_rate": 0.35,
                        "memory_usage_mb": 12.5,
                        "response_cache_size": 25,
                        "retrieval_cache_size": 20
                    }
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
    cache_stats: Optional[Dict[str, Any]] = Field(
        None,
        description="Cache statistics (Task 10: AC#2). Includes cache_size (total entries), hit_rate (0.0-1.0), memory_usage_mb (estimated), and separate counts for response and retrieval caches.",
        examples=[{
            "cache_size": 45,
            "hit_rate": 0.35,
            "memory_usage_mb": 12.5,
            "response_cache_size": 25,
            "retrieval_cache_size": 20
        }]
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


class RetrieveRequest(BaseModel):
    """
    Request model for document retrieval endpoint.

    Defines parameters for retrieving relevant documents to provide
    context to LLM for accurate responses.
    """
    query: str = Field(
        ...,
        description="Query for document retrieval",
        min_length=2,
        max_length=200,
        examples=["políticas de vacaciones", "procedimientos de contratación", "normas de seguridad"]
    )
    top_k: Optional[int] = Field(
        3,
        description="Number of documents to retrieve",
        ge=1,
        le=10,
        examples=[3, 5, 10]
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate query content."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()


class RetrieveResponse(BaseModel):
    """
    Response model for document retrieval endpoint.

    Contains retrieved documents with relevance scores and metadata
    for providing context to LLM.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "políticas de vacaciones",
                    "total_documents": 3,
                    "documents": [
                        {
                            "document_id": 1,
                            "title": "Política de Vacaciones Anuales",
                            "category": "RRHH",
                            "relevance_score": 0.95,
                            "snippet": "Los empleados tienen derecho a 15 días hábiles de <mark>vacaciones</mark> anuales...",
                            "upload_date": "2025-11-13T10:30:00Z"
                        }
                    ],
                    "optimized_query": "política OR regla OR directriz OR vacaciones OR descanso OR licencia",
                    "processing_time_ms": 45.2
                }
            ]
        }
    )

    query: str = Field(
        ...,
        description="Original query provided",
        examples=["políticas de vacaciones"]
    )
    optimized_query: Optional[str] = Field(
        None,
        description="Optimized query used for search with synonym expansion",
        examples=["política OR regla OR directriz OR vacaciones OR descanso OR licencia"]
    )
    total_documents: int = Field(
        ...,
        description="Total number of documents retrieved",
        ge=0,
        examples=[0, 3, 5]
    )
    documents: List[Dict[str, Any]] = Field(
        ...,
        description="List of retrieved documents with metadata"
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Time taken to process retrieval in milliseconds",
        ge=0,
        examples=[45.2, 120.5]
    )


class SourceInfo(BaseModel):
    """
    Source information in RAG response.

    AC#5: Structured source information returned with RAG answers,
    including document reference and relevance score.
    """
    document_id: int = Field(
        ...,
        description="ID of the source document",
        ge=1,
        examples=[1, 42, 123]
    )
    title: str = Field(
        ...,
        description="Title of the source document",
        examples=["Política de Vacaciones Anuales", "Procedimientos de Contratación"]
    )
    relevance_score: float = Field(
        ...,
        description="Relevance score (0.0-1.0) indicating how well the document matches the query",
        ge=0.0,
        le=1.0,
        examples=[0.95, 0.87, 0.72]
    )


class RAGRequest(BaseModel):
    """
    Request model for RAG query endpoint.

    AC#3: Defines parameters for RAG pipeline queries.
    """
    query: str = Field(
        ...,
        description="User's natural language query",
        min_length=2,
        max_length=500,
        examples=["¿Cuántos días de vacaciones tengo?", "¿Cuál es el procedimiento de contratación?"]
    )
    top_k: Optional[int] = Field(
        3,
        description="Number of documents to retrieve for context",
        ge=1,
        le=10,
        examples=[3, 5]
    )
    temperature: Optional[float] = Field(
        0.3,
        description="LLM temperature for response generation (0.0-1.0, lower = more deterministic)",
        ge=0.0,
        le=1.0,
        examples=[0.3, 0.7]
    )
    max_tokens: Optional[int] = Field(
        500,
        description="Maximum tokens in LLM response",
        ge=1,
        le=4096,
        examples=[500, 1000]
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate query content."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()


class RAGResponse(BaseModel):
    """
    Response model for RAG query endpoint.

    AC#5: Implements the complete response structure with answer,
    sources, and metadata about the generation process.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "answer": "Según la política de vacaciones, los empleados tienen derecho a 15 días hábiles anuales. Esto se especifica en el artículo 3 de la Política de Vacaciones Anuales.\n\n*Nota: Esta respuesta fue generada por IA. Verifica con tu supervisor si tienes dudas.*",
                    "sources": [
                        {
                            "document_id": 1,
                            "title": "Política de Vacaciones Anuales",
                            "relevance_score": 0.95
                        }
                    ],
                    "response_time_ms": 1245.5,
                    "documents_retrieved": 1
                },
                {
                    "answer": "Lo siento, no encontré documentos relevantes para tu consulta. Por favor, intenta formular la pregunta de otra manera.\n\n*Nota: Esta respuesta fue generada por IA. Verifica con tu supervisor si tienes dudas.*",
                    "sources": [],
                    "response_time_ms": 120.3,
                    "documents_retrieved": 0
                }
            ]
        }
    )

    answer: str = Field(
        ...,
        description="AI-generated answer grounded in retrieved documents. Includes disclaimer per AC#7.",
        examples=["Según los documentos, los empleados tienen derecho a 15 días de vacaciones anuales..."]
    )
    sources: List[SourceInfo] = Field(
        ...,
        description="List of source documents used to generate the answer. AC#5 structure.",
        examples=[[{
            "document_id": 1,
            "title": "Política de Vacaciones",
            "relevance_score": 0.95
        }]]
    )
    response_time_ms: float = Field(
        ...,
        description="Total response time in milliseconds. AC#8: metric for RNF2 (<2s P95).",
        ge=0,
        examples=[1245.5, 2000.0]
    )
    documents_retrieved: int = Field(
        ...,
        description="Number of documents retrieved in retrieval phase. AC#8: metric for logging.",
        ge=0,
        examples=[0, 3, 5]
    )


class QueryRequest(BaseModel):
    """
    Request model for conversational query endpoint.

    AC#2: Defines parameters for natural language queries with
    context mode selection and validation.
    """
    query: str = Field(
        ...,
        description="User's natural language query",
        min_length=10,
        max_length=500,
        examples=["¿Cuál es la política de vacaciones?", "Necesito información sobre procedimientos de contratación"]
    )
    context_mode: str = Field(
        "general",
        description="Context mode for retrieval (general: broad search, specific: focused search)",
        pattern="^(general|specific)$",
        examples=["general", "specific"]
    )
    top_k: Optional[int] = Field(
        3,
        description="Number of documents to retrieve for context",
        ge=1,
        le=10,
        examples=[3, 5]
    )
    temperature: Optional[float] = Field(
        0.7,
        description="LLM temperature for response generation (0.0-1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.7]
    )
    max_tokens: Optional[int] = Field(
        500,
        description="Maximum tokens in LLM response",
        ge=1,
        le=4096,
        examples=[500]
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate query content."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()


class QueryResponse(BaseModel):
    """
    Response model for conversational query endpoint.

    AC#5: Implements the complete response structure with answer,
    sources, metadata, and performance metrics.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "¿Cuál es la política de vacaciones?",
                    "answer": "Según la política de vacaciones, los empleados tienen derecho a 15 días hábiles anuales...",
                    "sources": [
                        {
                            "document_id": 1,
                            "title": "Política de Vacaciones Anuales",
                            "relevance_score": 0.95
                        }
                    ],
                    "response_time_ms": 1245.5,
                    "documents_retrieved": 1,
                    "timestamp": "2025-11-13T10:30:00Z"
                }
            ]
        }
    )

    query: str = Field(
        ...,
        description="Original query provided by user",
        examples=["¿Cuál es la política de vacaciones?"]
    )
    answer: str = Field(
        ...,
        description="AI-generated answer grounded in retrieved documents",
        examples=["Según los documentos, los empleados tienen derecho a 15 días de vacaciones anuales..."]
    )
    sources: List[SourceInfo] = Field(
        default_factory=list,
        description="List of source documents used to generate the answer. AC#5 structure.",
        examples=[[{
            "document_id": 1,
            "title": "Política de Vacaciones",
            "relevance_score": 0.95
        }]]
    )
    response_time_ms: float = Field(
        ...,
        description="Total response time in milliseconds. AC#5: metric for RNF2 (<2s P95).",
        ge=0,
        examples=[1245.5]
    )
    documents_retrieved: int = Field(
        ...,
        description="Number of documents retrieved in retrieval phase. AC#5: metric for logging.",
        ge=0,
        examples=[1, 3]
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of response generation in ISO format",
        examples=["2025-11-13T10:30:00Z"]
    )


class MetricsResponse(BaseModel):
    """
    Metrics endpoint response model (admin only).

    AC#9: Returns aggregated metrics over the last 24 hours,
    including query volume, response times (p50/p95/p99), and cache stats.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_queries": 156,
                    "avg_response_time_ms": 1245.7,
                    "p50_ms": 1100.0,
                    "p95_ms": 1950.0,
                    "p99_ms": 2100.0,
                    "cache_hit_rate": 0.15,
                    "avg_documents_retrieved": 2.8,
                    "period_hours": 24,
                    "generated_at": "2025-11-13T10:30:00Z"
                }
            ]
        }
    )

    total_queries: int = Field(
        ...,
        description="Total number of queries processed in the period",
        ge=0,
        examples=[156, 450, 1200]
    )
    avg_response_time_ms: float = Field(
        ...,
        description="Average response time in milliseconds",
        ge=0,
        examples=[1245.7, 1100.0, 2000.5]
    )
    p50_ms: float = Field(
        ...,
        description="50th percentile (median) response time in milliseconds",
        ge=0,
        examples=[1100.0, 950.0, 1500.0]
    )
    p95_ms: float = Field(
        ...,
        description="95th percentile response time in milliseconds (RNF2 target: <2000ms)",
        ge=0,
        examples=[1950.0, 1850.0, 1999.0]
    )
    p99_ms: float = Field(
        ...,
        description="99th percentile response time in milliseconds",
        ge=0,
        examples=[2100.0, 2200.0, 2500.0]
    )
    cache_hit_rate: float = Field(
        ...,
        description="Cache hit rate as a fraction (0.0-1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.15, 0.25, 0.42]
    )
    avg_documents_retrieved: float = Field(
        ...,
        description="Average number of documents retrieved per query",
        ge=0,
        examples=[2.8, 3.0, 2.5]
    )
    period_hours: int = Field(
        default=24,
        description="Time period for metrics in hours",
        ge=1,
        examples=[24, 168]
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when metrics were generated"
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


# Story 4.1: Summary Generation Schemas

class SummaryGenerationRequest(BaseModel):
    """
    Request model for document summary generation endpoint (Story 4.1, AC1, AC2).

    Specifies which document to summarize and desired summary length.
    """
    document_id: int = Field(
        ...,
        description="ID of the document to summarize",
        ge=1,
        examples=[1, 42]
    )
    summary_length: str = Field(
        ...,
        description="Desired summary length: short (150 words), medium (300 words), or long (500 words)",
        pattern="^(short|medium|long)$",
        examples=["short", "medium", "long"]
    )

    @field_validator('summary_length')
    @classmethod
    def validate_summary_length(cls, v):
        """Validate summary_length is one of allowed values."""
        if v not in {"short", "medium", "long"}:
            raise ValueError("summary_length must be 'short', 'medium', or 'long'")
        return v


class SummaryGenerationResponse(BaseModel):
    """
    Response model for document summary generation endpoint (Story 4.1, AC3).

    Contains the generated summary along with metadata about generation.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "document_id": 1,
                    "document_title": "Política de Vacaciones Anuales",
                    "summary": "La compañía otorga 15 días hábiles de vacaciones anuales a todos los empleados...\n*Resumen generado automáticamente por IA. Revisa el documento completo para detalles precisos.*",
                    "summary_length": "medium",
                    "word_count": 289,
                    "generated_at": "2025-11-14T10:30:00Z",
                    "generation_time_ms": 2345.5
                }
            ]
        }
    )

    document_id: int = Field(
        ...,
        description="ID of the summarized document",
        ge=1,
        examples=[1]
    )
    document_title: str = Field(
        ...,
        description="Title of the document",
        examples=["Política de Vacaciones Anuales"]
    )
    summary: str = Field(
        ...,
        description="Generated summary text with disclaimer appended (AC7)",
        examples=["La compañía otorga 15 días hábiles de vacaciones..."]
    )
    summary_length: str = Field(
        ...,
        description="Requested summary length",
        pattern="^(short|medium|long)$",
        examples=["medium"]
    )
    word_count: int = Field(
        ...,
        description="Word count of the generated summary",
        ge=0,
        examples=[289]
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp when summary was generated",
        examples=["2025-11-14T10:30:00Z"]
    )
    generation_time_ms: float = Field(
        ...,
        description="Time taken to generate summary in milliseconds",
        ge=0,
        examples=[2345.5]
    )