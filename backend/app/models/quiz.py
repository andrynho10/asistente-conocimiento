"""
Modelos SQLModel para generación automática de quizzes
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .document import Document
    from .user import User


class DifficultyLevel(str, Enum):
    """Niveles de dificultad para preguntas"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuizBase(SQLModel):
    """Base model para Quiz con campos comunes"""
    document_id: int = Field(foreign_key="documents.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str
    difficulty: DifficultyLevel = Field(index=True)
    num_questions: int
    is_validated: bool = Field(default=False)


class Quiz(QuizBase, table=True):
    """Modelo de quiz persistente en base de datos"""
    __tablename__ = "quiz"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    # NOTE: Relationships intentionally omitted to avoid circular imports


class QuizCreate(QuizBase):
    """Schema para crear nuevo quiz"""
    pass


class QuizRead(QuizBase):
    """Schema para leer datos de quiz"""
    id: int
    created_at: datetime


class QuizUpdate(SQLModel):
    """Schema para actualizar quiz"""
    title: str | None = Field(default=None)
    is_validated: bool | None = Field(default=None)


class QuizQuestionBase(SQLModel):
    """Base model para QuizQuestion con campos comunes"""
    quiz_id: int = Field(foreign_key="quiz.id", index=True)
    question: str = Field(sa_column=Text())
    options_json: list[str] = Field(sa_type=JSON)  # Array de 4 opciones
    correct_answer: str
    explanation: str = Field(sa_column=Text())
    difficulty: DifficultyLevel
    topic: str | None = Field(default=None)


class QuizQuestion(QuizQuestionBase, table=True):
    """Modelo de pregunta de quiz persistente en base de datos"""
    __tablename__ = "quiz_questions"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )


class QuizQuestionCreate(QuizQuestionBase):
    """Schema para crear nueva pregunta de quiz"""
    pass


class QuizQuestionRead(QuizQuestionBase):
    """Schema para leer datos de pregunta de quiz"""
    id: int
    created_at: datetime


class QuizQuestionUpdate(SQLModel):
    """Schema para actualizar pregunta de quiz"""
    question: str | None = Field(default=None, sa_column=Text())
    options_json: list[str] | None = Field(default=None)
    correct_answer: str | None = Field(default=None)
    explanation: str | None = Field(default=None)
    difficulty: DifficultyLevel | None = Field(default=None)
    topic: str | None = Field(default=None)
