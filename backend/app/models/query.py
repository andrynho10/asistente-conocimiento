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
