"""
Modelo de documento para el sistema de asistente de conocimiento
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class DocumentBase(SQLModel):
    """Base model para Document con campos comunes"""
    title: str = Field(max_length=255)
    category: str = Field(max_length=100, default="General")
    file_size: int = Field(ge=0)  # ge = greater or equal (tamaño >= 0)
    status: str = Field(default="active", max_length=20)


class Document(DocumentBase, table=True):
    """Modelo de documento persistente en base de datos"""
    id: int | None = Field(default=None, primary_key=True)
    file_path: str = Field(unique=True, max_length=500)
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="user.id")

    # Relación con usuario
    user: "User" = Relationship(back_populates="documents")


class DocumentCreate(DocumentBase):
    """Schema para crear un nuevo documento"""
    file_path: str = Field(max_length=500)
    user_id: int


class DocumentRead(DocumentBase):
    """Schema para leer datos de documento"""
    id: int
    file_path: str
    upload_date: datetime
    user_id: int


class DocumentUpdate(SQLModel):
    """Schema para actualizar un documento existente"""
    title: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=20)