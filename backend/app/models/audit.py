"""
Modelo de auditoría para el sistema de asistente de conocimiento
Cumple con requerimientos de cumplimiento normativo Ley 19.628
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class AuditLogBase(SQLModel):
    """Base model para AuditLog con campos comunes"""
    action: str = Field(max_length=100)
    resource_type: str = Field(max_length=50)
    resource_id: Optional[int] = Field(default=None)
    details: Optional[str] = Field(default=None, max_length=1000)
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 puede tener hasta 45 chars


class AuditLog(AuditLogBase, table=True):
    """Modelo de registro de auditoría persistente en base de datos"""
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relación con usuario
    user: "User" = Relationship(back_populates="audit_logs")


class AuditLogCreate(AuditLogBase):
    """Schema para crear un nuevo registro de auditoría"""
    user_id: int


class AuditLogRead(AuditLogBase):
    """Schema para leer datos de auditoría"""
    id: int
    user_id: int
    timestamp: datetime


# Constantes para tipos de acción y recursos
class AuditAction:
    """Constantes para acciones de auditoría"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    PASSWORD_CHANGE = "password_change"


class AuditResourceType:
    """Constantes para tipos de recursos de auditoría"""
    USER = "user"
    DOCUMENT = "document"
    SESSION = "session"
    SYSTEM = "system"