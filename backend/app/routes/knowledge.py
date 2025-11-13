from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlmodel import Session, select
from typing import Optional
import os
import re
from datetime import datetime
from app.database import get_session
from app.middleware.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.document import Document, DocumentCategory, DocumentStatusResponse
from app.models.audit import AuditLog, AuditLogCreate
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/knowledge", tags=["knowledge management"])

# Configuración
ALLOWED_EXTENSIONS = {'.pdf', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = "/uploads"

def sanitize_filename(title: str) -> str:
    """Sanitiza título para usar como nombre de archivo"""
    # Remover caracteres especiales, reemplazar espacios con guiones bajos
    sanitized = re.sub(r'[^\w\s-]', '', title.strip())
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized

def validate_file_format(file: UploadFile) -> bool:
    """Valida que el archivo sea PDF o TXT"""
    if not file.filename:
        return False

    # Validar extensión
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False

    # Validar MIME type (pero no confiar ciegamente en él)
    allowed_mime_types = {
        '.pdf': ['application/pdf'],
        '.txt': ['text/plain']
    }

    if file_ext in allowed_mime_types:
        return file.content_type in allowed_mime_types[file_ext]

    return False

async def validate_file_size(file: UploadFile) -> bool:
    """Valida que el archivo no exceda 10MB"""
    # Leer el archivo en chunks para verificar tamaño
    content = await file.read()
    file.file.seek(0)  # Reset file pointer
    return len(content) <= MAX_FILE_SIZE

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para cargar documentos con validación
    Solo usuarios con rol admin pueden usar este endpoint
    """

    # AC 5: Validar rol de administrador
    if current_user.role.value != UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INSUFFICIENT_PERMISSIONS",
                "message": "Permisos insuficientes"
            }
        )

    # AC 2: Validar formato de archivo
    if not validate_file_format(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FILE_FORMAT",
                "message": "Solo se permiten archivos PDF y TXT"
            }
        )

    # AC 3: Validar tamaño de archivo
    if not await validate_file_size(file):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": "El archivo excede el tamaño máximo de 10MB"
            }
        )

    # AC 4: Validar que la categoría exista
    category_statement = select(DocumentCategory).where(
        DocumentCategory.name == category
    )
    existing_category = db.exec(category_statement).first()

    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_CATEGORY",
                "message": f"La categoría '{category}' no existe"
            }
        )

    # AC 6: Almacenar archivo con nombre único
    try:
        # Crear directorio uploads si no existe
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Generar nombre único
        sanitized_title = sanitize_filename(title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{sanitized_title}_{timestamp}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Guardar archivo
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        file_size_bytes = len(content)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File storage error"
        )

    # AC 7: Crear registro en base de datos
    try:
        document = Document(
            title=title,
            description=description,
            category=category,
            file_type=file_ext[1:],  # Sin el punto
            file_size_bytes=file_size_bytes,
            file_path=file_path,
            uploaded_by=current_user.id,
            is_indexed=False  # AC 7: False para procesamiento posterior
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        document_id = document.id

    except Exception as e:
        # Si falla la DB, eliminar el archivo guardado
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

    # AC 8: Registrar auditoría
    try:
        audit_log = AuditLogCreate(
            user_id=current_user.id,
            action="DOCUMENT_UPLOADED",
            resource_type="document",
            resource_id=document_id,
            details=f"Document '{title}' uploaded to category '{category}'"
        )

        audit_entry = AuditLog.model_validate(audit_log)
        db.add(audit_entry)
        db.commit()

    except Exception as e:
        # No fallar el endpoint si auditoría falla, pero loggear error
        print(f"Error creating audit log: {e}")

    # AC3: Agregar extracción de texto en background
    # Crear una nueva sesión de DB para el background task
    def extract_text_task():
        from app.database import engine
        from sqlmodel import Session
        import asyncio
        with Session(engine) as task_db:
            asyncio.run(DocumentService.extract_text(document_id, task_db))

    background_tasks.add_task(extract_text_task)

    # AC 1: Respuesta exitosa (retorna inmediatamente sin esperar extracción)
    return {
        "document_id": document_id,
        "title": title,
        "file_path": file_path,
        "status": "uploaded",
        "message": "Documento cargado exitosamente"
    }


@router.get("/documents/{id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para consultar el estado de indexación de un documento.

    AC4: Retorna información sobre si el documento ha sido indexado,
    cuándo fue indexado, y el estado actual del proceso.

    Args:
        id: ID del documento a consultar
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        DocumentStatusResponse: Estado de indexación del documento

    Raises:
        HTTPException 404: Si el documento no existe
    """
    # AC4: Consultar Document por ID
    statement = select(Document).where(Document.id == id)
    document = db.exec(statement).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Documento con ID {id} no encontrado"
            }
        )

    # AC4: Determinar status según is_indexed
    if document.is_indexed:
        doc_status = "indexed"
    else:
        # Si content_text es None, aún no ha sido procesado
        doc_status = "processing"

    # AC4: Retornar DocumentStatusResponse
    return DocumentStatusResponse(
        document_id=document.id,
        title=document.title,
        is_indexed=document.is_indexed,
        indexed_at=document.indexed_at,
        status=doc_status
    )