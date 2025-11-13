from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from typing import Optional
import os
import re
from datetime import datetime
from app.database import get_session
from app.middleware.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.document import Document, DocumentCategory, DocumentStatusResponse, SearchResponse, DocumentResponse, DocumentListRequest, CategoryResponse
from app.models.audit import AuditLog, AuditLogCreate
from app.services.document_service import DocumentService
from app.services.search_service import SearchService

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


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint de búsqueda full-text sobre documentos indexados.

    Permite buscar documentos por palabras clave en título y contenido,
    retornando resultados ordenados por relevancia con snippets de contexto.

    AC3: Endpoint GET /api/knowledge/search con autenticación requerida
    AC4: Soporte para palabras clave, frases exactas y operadores booleanos
    AC5: Resultados incluyen snippets y paginación

    Args:
        q: Query de búsqueda (mínimo 2 caracteres, máximo 200)
        limit: Número máximo de resultados (1-100, default 20)
        offset: Offset para paginación (default 0)
        db: Sesión de base de datos
        current_user: Usuario autenticado (requerido)

    Returns:
        SearchResponse: Resultados de búsqueda con query, total y lista de documentos

    Raises:
        HTTPException 400: Si query es inválida (muy corta o muy larga)
        HTTPException 500: Si hay error interno en búsqueda FTS5

    Examples:
        GET /api/knowledge/search?q=vacaciones
        GET /api/knowledge/search?q="políticas de RRHH"&limit=10
        GET /api/knowledge/search?q=reembolso AND urgente&offset=20
    """
    try:
        # AC3: Autenticación ya validada por Depends(get_current_user)
        # AC4: SearchService maneja palabras clave, frases y operadores
        results = await SearchService.search_documents(
            query=q,
            limit=limit,
            offset=offset,
            db=db
        )

        return results

    except ValueError as e:
        # AC7: Manejo de errores de validación (query muy corta/larga)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_QUERY",
                "message": str(e)
            }
        )
    except Exception as e:
        # AC7: Manejo de errores internos con logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SEARCH_ERROR",
                "message": "Error interno en búsqueda"
            }
        )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "upload_date",
    order: str = "desc",
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para listar documentos con filtros, paginación y ordenamiento.

    AC1: Listado de Documentos con Paginación (GET /api/knowledge/documents)
    - Por defecto: limit=20, offset=0
    - Retorna response 200 con lista de DocumentResponse

    AC2: Filtros de Búsqueda
    - category: filtrar por categoría específica
    - limit, offset: paginación
    - sort_by: upload_date, title, file_size_bytes
    - order: asc, desc

    AC5: Ordenamiento soporta upload_date, title, file_size_bytes

    Args:
        category: Filtro opcional por categoría
        limit: Límite de resultados (default: 20, max: 100)
        offset: Offset para paginación (default: 0)
        sort_by: Campo de ordenamiento (upload_date, title, file_size_bytes)
        order: Dirección de ordenamiento (asc, desc)
        db: Sesión de base de datos
        current_user: Usuario autenticado (admin o user)

    Returns:
        list[DocumentResponse]: Lista de documentos con uploaded_by como username

    Raises:
        HTTPException 400: Si los parámetros de ordenamiento son inválidos
        HTTPException 500: Error interno del servidor
    """
    try:
        # AC6: Usuario 'user' puede listar documentos (solo lectura)
        document_list_request = DocumentListRequest(
            category=category,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order
        )

        documents = await DocumentService.get_documents(
            db=db,
            category=document_list_request.category,
            limit=document_list_request.limit,
            offset=document_list_request.offset,
            sort_by=document_list_request.sort_by,
            order=document_list_request.order
        )

        return documents

    except ValueError as e:
        # Error de validación de parámetros
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PARAMETERS",
                "message": str(e)
            }
        )
    except Exception as e:
        # Error genérico del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "Error interno del servidor"
            }
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obtener detalles de un documento específico.

    AC3: Detalle de Documento (GET /api/knowledge/documents/{document_id})
    - Retorna detalles completos del documento
    - Retorna 404 si no existe

    Args:
        document_id: ID del documento a consultar
        db: Sesión de base de datos
        current_user: Usuario autenticado (admin o user)

    Returns:
        DocumentResponse: Detalles completos del documento

    Raises:
        HTTPException 404: Si el documento no existe
        HTTPException 500: Error interno del servidor
    """
    try:
        document = await DocumentService.get_document_by_id(document_id, db)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DOCUMENT_NOT_FOUND",
                    "message": f"Documento con ID {document_id} no encontrado"
                }
            )

        return document

    except HTTPException:
        # Re-raise HTTP exceptions (como 404)
        raise
    except Exception as e:
        # Error genérico del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "Error interno del servidor"
            }
        )


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para listar categorías con contador de documentos.

    AC4: Listado de Categorías (GET /api/knowledge/categories)
    - Retorna lista de categorías con contador de documentos

    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado (admin o user)

    Returns:
        list[CategoryResponse]: Lista de categorías con document_count

    Raises:
        HTTPException 500: Error interno del servidor
    """
    try:
        categories = await DocumentService.get_categories(db)
        return categories

    except Exception as e:
        # Error genérico del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "Error interno del servidor"
            }
        )

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para descargar documentos del repositorio.

    AC1: GET /api/knowledge/documents/{document_id}/download retorna archivo binario
    AC2: 404 si documento no existe, 401 si no autenticado
    AC3: Elimina registros huérfanos, sanitiza filename, valida path

    Args:
        document_id: ID del documento a descargar
        request: Request object para obtener IP address
        db: Sesión de base de datos
        current_user: Usuario autenticado (admin o user)

    Returns:
        FileResponse: Archivo binario con headers correctos

    Raises:
        HTTPException 404: Si el documento no existe o archivo huérfano
        HTTPException 500: Error interno del servidor
    """
    try:
        # Obtener información de descarga desde DocumentService
        download_info = await DocumentService.download_document(document_id, db)

        if not download_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DOCUMENT_NOT_FOUND",
                    "message": "El documento solicitado no existe"
                }
            )

        file_path, file_type, safe_filename, file_size = download_info

        # Determinar Content-Type según file_type
        content_type_map = {
            'pdf': 'application/pdf',
            'txt': 'text/plain'
        }
        media_type = content_type_map.get(file_type, 'application/octet-stream')

        # Validar que el path esté dentro del directorio uploads permitido
        # Prevenir directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIR)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DOCUMENT_NOT_FOUND",
                    "message": "El documento solicitado no existe"
                }
            )

        # Registrar auditoría de descarga
        try:
            ip_address = request.client.host if request.client else "unknown"
            audit_log = AuditLogCreate(
                user_id=current_user.id,
                action="DOCUMENT_DOWNLOADED",
                resource_type="document",
                resource_id=document_id,
                ip_address=ip_address,
                details=f"Document '{safe_filename}' downloaded by user {current_user.username}"
            )

            audit_entry = AuditLog.model_validate(audit_log)
            db.add(audit_entry)
            db.commit()

        except Exception as e:
            # No fallar el endpoint si auditoría falla, pero loggear error
            print(f"Error creating audit log: {e}")

        # Retornar FileResponse con headers correctos
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=safe_filename
        )

    except HTTPException:
        # Re-raise HTTP exceptions (como 404)
        raise
    except Exception as e:
        # Error genérico del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "Error interno del servidor"
            }
        )


@router.get("/documents/{document_id}/preview")
async def preview_document(
    document_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obtener vista previa de documento (primeros 500 caracteres).

    AC5: GET /api/knowledge/documents/{document_id}/preview retorna primeros 500 caracteres

    Args:
        document_id: ID del documento a previsualizar
        db: Sesión de base de datos
        current_user: Usuario autenticado (admin o user)

    Returns:
        dict: Preview del documento con primeros 500 caracteres

    Raises:
        HTTPException 404: Si el documento no existe
        HTTPException 500: Error interno del servidor
    """
    try:
        # Obtener preview desde DocumentService
        preview_text = await DocumentService.get_document_preview(document_id, db)

        if preview_text is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DOCUMENT_NOT_FOUND",
                    "message": "El documento solicitado no existe o no tiene contenido extraído"
                }
            )

        return {
            "document_id": document_id,
            "preview": preview_text,
            "preview_length": len(preview_text),
            "message": "Preview del documento"
        }

    except HTTPException:
        # Re-raise HTTP exceptions (como 404)
        raise
    except Exception as e:
        # Error genérico del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "Error interno del servidor"
            }
        )
