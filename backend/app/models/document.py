"""
Modelo de documento para el sistema de asistente de conocimiento
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class SortByEnum(str, Enum):
    """Enum para campos permitidos en ordenamiento de documentos"""
    UPLOAD_DATE = "upload_date"
    TITLE = "title"
    FILE_SIZE_BYTES = "file_size_bytes"


class OrderEnum(str, Enum):
    """Enum para dirección de ordenamiento"""
    ASC = "asc"
    DESC = "desc"


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


class DocumentStatusResponse(SQLModel):
    """Schema para respuesta de estado de indexación de documento"""
    document_id: int
    title: str
    is_indexed: bool
    indexed_at: datetime | None = None
    status: str  # 'indexed', 'processing', 'error'


# Schemas para búsqueda full-text
class SearchRequest(SQLModel):
    """Schema para request de búsqueda full-text"""
    q: str = Field(min_length=2, max_length=200, description="Query de búsqueda")
    limit: int = Field(default=20, ge=1, le=100, description="Número máximo de resultados")
    offset: int = Field(default=0, ge=0, description="Offset para paginación")


class SearchResult(SQLModel):
    """Schema para un resultado individual de búsqueda"""
    document_id: int
    title: str
    category: str
    relevance_score: float = Field(ge=0.0, le=1.0, description="Score de relevancia normalizado")
    snippet: str | None = Field(default=None, description="Fragmento de contexto con la coincidencia")
    upload_date: datetime


class SearchResponse(SQLModel):
    """Schema para respuesta completa de búsqueda"""
    query: str
    total_results: int
    results: list[SearchResult]


# Schemas para listado y consulta de documentos (Story 2.5)
class DocumentResponse(SQLModel):
    """Schema para respuesta de documento con uploaded_by como username"""
    id: int
    title: str
    description: str | None
    category: str
    file_type: str
    file_size_bytes: int
    upload_date: datetime
    uploaded_by: str  # Username instead of user_id
    is_indexed: bool
    indexed_at: datetime | None

    model_config = {"from_attributes": True}


class DocumentListRequest(SQLModel):
    """Schema para query params de listado de documentos"""
    category: str | None = Field(default=None, description="Filtrar por categoría")
    limit: int = Field(default=20, ge=1, le=100, description="Límite de resultados")
    offset: int = Field(default=0, ge=0, description="Offset para paginación")
    sort_by: SortByEnum = Field(
        default=SortByEnum.UPLOAD_DATE,
        description="Campo de ordenamiento permitido"
    )
    order: OrderEnum = Field(
        default=OrderEnum.DESC,
        description="Dirección de ordenamiento"
    )


class CategoryResponse(SQLModel):
    """Schema para respuesta de categoría con contador de documentos"""
    name: str
    description: str | None
    document_count: int

    model_config = {"from_attributes": True}