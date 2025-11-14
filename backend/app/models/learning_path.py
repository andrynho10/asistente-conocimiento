"""
Modelos SQLModel para generación automática de rutas de aprendizaje (Learning Paths)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Text
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from .user import User


class UserLevel(str, Enum):
    """Niveles de usuario para rutas de aprendizaje"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningPathBase(SQLModel):
    """Base model para LearningPath con campos comunes"""
    user_id: int = Field(foreign_key="user.id", index=True)
    topic: str = Field(index=True)
    user_level: UserLevel = Field(index=True)
    content_json: dict[str, Any] = Field(sa_type=JSON)


class LearningPath(LearningPathBase, table=True):
    """Modelo de ruta de aprendizaje persistente en base de datos"""
    __tablename__ = "learning_paths"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    # NOTE: Relationships intentionally omitted to avoid circular imports


class LearningPathCreate(LearningPathBase):
    """Schema para crear nueva ruta de aprendizaje"""
    pass


class LearningPathRead(LearningPathBase):
    """Schema para leer datos de ruta de aprendizaje"""
    id: int
    created_at: datetime


class LearningPathUpdate(SQLModel):
    """Schema para actualizar ruta de aprendizaje"""
    content_json: dict[str, Any] | None = Field(default=None)


class LearningPathProgressBase(SQLModel):
    """Base model para LearningPathProgress con campos comunes"""
    path_id: int = Field(foreign_key="generated_content.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    completed_steps: int = Field(default=0)
    last_step: int = Field(default=0)


class LearningPathProgress(LearningPathProgressBase, table=True):
    """Modelo de progreso de ruta de aprendizaje persistente en base de datos"""
    __tablename__ = "learning_path_progress"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


class LearningPathProgressCreate(LearningPathProgressBase):
    """Schema para crear nuevo progreso de ruta de aprendizaje"""
    pass


class LearningPathProgressRead(LearningPathProgressBase):
    """Schema para leer datos de progreso de ruta de aprendizaje"""
    id: int
    created_at: datetime
    updated_at: datetime


class LearningPathProgressUpdate(SQLModel):
    """Schema para actualizar progreso de ruta de aprendizaje"""
    completed_steps: int | None = Field(default=None)
    last_step: int | None = Field(default=None)
