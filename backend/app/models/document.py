"""
Modelo de documento para el sistema de asistente de conocimiento
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class DocumentCategory(SQLModel, table=True):
    """Modelo de categoría de documento"""
    __tablename__ = "document_categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    description: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentBase(SQLModel):
    """Base model para Document con campos comunes"""
    title: str = Field(max_length=200, index=True)
    description: str | None = Field(default=None)
    category: str = Field(max_length=100, index=True)
    file_type: str = Field(max_length=10)  # 'pdf' o 'txt'
    file_size_bytes: int


class Document(DocumentBase, table=True):
    """Modelo de documento persistente en base de datos"""
    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)
    file_path: str = Field(max_length=500, unique=True)
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    uploaded_by: int = Field(foreign_key="user.id")
    content_text: str | None = Field(default=None)
    is_indexed: bool = Field(default=False)
    indexed_at: datetime | None = Field(default=None)

    # Relación con usuario
    user: "User" = Relationship(back_populates="documents")


class DocumentCreate(DocumentBase):
    """Schema para crear un nuevo documento"""
    file_path: str = Field(max_length=500)
    uploaded_by: int


class DocumentRead(DocumentBase):
    """Schema para leer datos de documento"""
    id: int
    file_path: str
    upload_date: datetime
    uploaded_by: int
    content_text: str | None
    is_indexed: bool
    indexed_at: datetime | None


class DocumentUpdate(SQLModel):
    """Schema para actualizar un documento existente"""
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None)
    category: str | None = Field(default=None, max_length=100)
    file_type: str | None = Field(default=None, max_length=10)
    content_text: str | None = Field(default=None)
    is_indexed: bool | None = Field(default=None)
    indexed_at: datetime | None = Field(default=None)


# Schemas para DocumentCategory
class DocumentCategoryBase(SQLModel):
    """Base model para DocumentCategory con campos comunes"""
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)


class DocumentCategoryCreate(DocumentCategoryBase):
    """Schema para crear una nueva categoría de documento"""
    pass


class DocumentCategoryRead(DocumentCategoryBase):
    """Schema para leer datos de categoría de documento"""
    id: int
    created_at: datetime


class DocumentCategoryUpdate(SQLModel):
    """Schema para actualizar una categoría de documento existente"""
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None)