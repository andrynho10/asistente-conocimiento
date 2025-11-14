"""
Modelos SQLModel para el sistema de asistente de conocimiento
"""

from .user import User, UserCreate, UserRead, UserUpdate, UserRole
from .document import (
    Document,
    DocumentCreate,
    DocumentRead,
    DocumentUpdate,
    DocumentCategory,
    DocumentCategoryCreate,
    DocumentCategoryRead,
    DocumentCategoryUpdate,
    SortByEnum,
    OrderEnum
)
from .audit import (
    AuditLog,
    AuditLogCreate,
    AuditLogRead,
    AuditAction,
    AuditResourceType
)
from .generated_content import (
    GeneratedContent,
    GeneratedContentCreate,
    GeneratedContentRead,
    GeneratedContentUpdate,
    ContentType
)
from .quiz import (
    Quiz,
    QuizCreate,
    QuizRead,
    QuizUpdate,
    QuizQuestion,
    QuizQuestionCreate,
    QuizQuestionRead,
    QuizQuestionUpdate,
    DifficultyLevel
)

__all__ = [
    # User models
    "User",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserRole",

    # Document models
    "Document",
    "DocumentCreate",
    "DocumentRead",
    "DocumentUpdate",
    "DocumentCategory",
    "DocumentCategoryCreate",
    "DocumentCategoryRead",
    "DocumentCategoryUpdate",
    "SortByEnum",
    "OrderEnum",

    # Audit models
    "AuditLog",
    "AuditLogCreate",
    "AuditLogRead",
    "AuditAction",
    "AuditResourceType",

    # Generated Content models
    "GeneratedContent",
    "GeneratedContentCreate",
    "GeneratedContentRead",
    "GeneratedContentUpdate",
    "ContentType",

    # Quiz models
    "Quiz",
    "QuizCreate",
    "QuizRead",
    "QuizUpdate",
    "QuizQuestion",
    "QuizQuestionCreate",
    "QuizQuestionRead",
    "QuizQuestionUpdate",
    "DifficultyLevel",
]