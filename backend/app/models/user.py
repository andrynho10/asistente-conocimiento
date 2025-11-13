"""
Modelo de usuario para el sistema de asistente de conocimiento
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .audit import AuditLog
    from .document import Document
    from .query import Query


class UserRole(str, Enum):
    """Enum para roles de usuario"""
    admin = "admin"
    user = "user"


class UserBase(SQLModel):
    """Base model para User con campos comunes"""
    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.user)
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    """Modelo de usuario persistente en base de datos"""
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relaciones
    documents: List["Document"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    """Schema para crear un nuevo usuario"""
    password: str = Field(min_length=8, max_length=255)


class UserRead(UserBase):
    """Schema para leer datos de usuario (sin password)"""
    id: int
    created_at: datetime
    updated_at: datetime


class UserUpdate(SQLModel):
    """Schema para actualizar un usuario existente"""
    username: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=255)