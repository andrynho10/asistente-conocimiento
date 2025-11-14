"""
Query Model - RAG Query Audit and Logging

Tracks all RAG queries executed by users for audit trail,
performance monitoring, and caching optimization.

AC#8: Logging metrics for RAG responses including:
- query_text: User's original query
- answer_text: AI-generated answer
- sources_json: Retrieved document sources
- response_time_ms: Response time metric
- user_id: User who made the query
- created_at: Timestamp of query execution
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class QueryBase(SQLModel):
    """Base model for Query with common fields"""
    query_text: str = Field(max_length=500, index=True)
    answer_text: str
    sources_json: str  # JSON array of {document_id, title, relevance_score}
    response_time_ms: float = Field(ge=0)


class Query(QueryBase, table=True):
    """RAG Query persistent database model"""
    __tablename__ = "queries"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    # NOTE: Relationship with user intentionally omitted to avoid circular imports
    # Query is referenced primarily for audit logging, not relational queries


class QueryCreate(QueryBase):
    """Schema for creating a new query record"""
    user_id: int


class QueryRead(QueryBase):
    """Schema for reading query data"""
    id: int
    user_id: int
    created_at: datetime


class PerformanceMetricBase(SQLModel):
    """Base model for PerformanceMetric with common fields"""
    retrieval_time_ms: float = Field(ge=0)
    llm_time_ms: float = Field(ge=0)
    total_time_ms: float = Field(ge=0)
    cache_hit: bool = False


class PerformanceMetric(PerformanceMetricBase, table=True):
    """Performance metrics for RAG queries

    AC#8: Stores timing data for retrieval and LLM generation phases
    - retrieval_time_ms: Time spent retrieving documents from database
    - llm_time_ms: Time spent generating response with LLM
    - total_time_ms: Total end-to-end response time
    - cache_hit: Whether the response was served from cache
    - query_id: Foreign key to the Query record
    """
    __tablename__ = "performance_metrics"

    id: int | None = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="queries.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )


class PerformanceMetricCreate(PerformanceMetricBase):
    """Schema for creating a new performance metric record"""
    query_id: int


class PerformanceMetricRead(PerformanceMetricBase):
    """Schema for reading performance metric data"""
    id: int
    query_id: int
    created_at: datetime
