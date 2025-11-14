"""
Admin Dashboard Schemas

Pydantic models for admin endpoints request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GeneratedContentFilter(BaseModel):
    """Filter parameters for listing generated content"""
    type: Optional[str] = None
    document_id: Optional[int] = None
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    limit: int = 20
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"


class GeneratedContentValidateRequest(BaseModel):
    """Request body for content validation"""
    is_validated: bool


class QuizAttemptResponse(BaseModel):
    """Quiz attempt stats"""
    quiz_id: int
    total_attempts: int
    avg_score_percentage: float
    pass_rate: float
    most_difficult_question: Optional[dict] = None


class LearningPathStatsResponse(BaseModel):
    """Learning path progress stats"""
    path_id: int
    total_views: int
    completed_count: int
    completion_rate: float
    most_skipped_step: Optional[str] = None


class AdminAuditLogResponse(BaseModel):
    """Admin action audit log entry"""
    user_id: int
    action: str
    resource_type: str
    resource_id: int
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    timestamp: datetime
