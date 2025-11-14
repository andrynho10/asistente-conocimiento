"""
Modelo de contenido generado por IA para el sistema de asistente de conocimiento
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .document import Document
    from .user import User


class ContentType(str, Enum):
    """Tipos de contenido generado"""
    SUMMARY = "summary"
    QUIZ = "quiz"
    LEARNING_PATH = "learning_path"


class GeneratedContentBase(SQLModel):
    """Base model para GeneratedContent con campos comunes"""
    document_id: int = Field(foreign_key="documents.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    content_type: ContentType = Field(index=True)
    content_json: dict[str, Any] = Field(sa_type=JSON)


class GeneratedContent(GeneratedContentBase, table=True):
    """Modelo de contenido generado persistente en base de datos"""
    __tablename__ = "generated_content"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Admin validation fields (Story 4.5)
    is_validated: bool = Field(default=False, index=True)
    validated_by: int | None = Field(default=None, foreign_key="user.id", nullable=True)
    validated_at: datetime | None = Field(default=None, nullable=True)

    # Soft delete support (Story 4.5)
    deleted_at: datetime | None = Field(default=None, index=True, nullable=True)

    # NOTE: Relationships intentionally omitted to avoid circular imports
    # GeneratedContent is referenced primarily for caching, not relational queries


class GeneratedContentCreate(GeneratedContentBase):
    """Schema para crear nuevo contenido generado"""
    pass


class GeneratedContentRead(GeneratedContentBase):
    """Schema para leer datos de contenido generado"""
    id: int
    created_at: datetime
    is_validated: bool
    validated_by: int | None = None
    validated_at: datetime | None = None
    deleted_at: datetime | None = None


class GeneratedContentUpdate(SQLModel):
    """Schema para actualizar contenido generado"""
    content_json: dict[str, Any] | None = Field(default=None)


class GeneratedContentAdminValidate(SQLModel):
    """Schema para validación de contenido por admin"""
    is_validated: bool
