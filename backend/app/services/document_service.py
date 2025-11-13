"""
Servicio para gestión y procesamiento de documentos.

Orquesta la extracción de texto de documentos cargados y actualiza
el estado de indexación en la base de datos.
"""

import logging
import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Session, select, func

from app.models.document import Document, DocumentCategory, DocumentResponse, CategoryResponse
from app.models.user import User
from app.utils.pdf_extractor import extract_text_from_pdf, extract_text_from_txt

# Configurar logging estructurado
logger = logging.getLogger(__name__)


class DocumentService:
    """
    Servicio para operaciones de documentos y extracción de texto.

    Proporciona métodos para extraer texto de documentos PDF y TXT,
    actualizando el estado de indexación en la base de datos.
    """

    @staticmethod
    async def extract_text(document_id: int, db: Session) -> bool:
        """
        Extrae texto de un documento y actualiza su estado en la base de datos.

        Este método orquesta el proceso completo de extracción:
        1. Obtiene el documento de la base de datos
        2. Determina el tipo de archivo (pdf/txt)
        3. Llama a la función extractora apropiada
        4. Actualiza los campos content_text, is_indexed, indexed_at
        5. Registra métricas en logs estructurados

        Args:
            document_id: ID del documento a procesar
            db: Sesión de base de datos SQLModel

        Returns:
            bool: True si la extracción fue exitosa, False en caso de error

        Example:
            >>> async with get_session() as db:
            >>>     success = await DocumentService.extract_text(123, db)
            >>>     assert success is True
        """
        start_time = datetime.now()

        try:
            # AC: Obtener Document desde DB
            statement = select(Document).where(Document.id == document_id)
            document = db.exec(statement).first()

            if not document:
                error_msg = f"Documento no encontrado: ID {document_id}"
                logger.error(json.dumps({
                    "event": "extraction_error",
                    "document_id": document_id,
                    "error": error_msg,
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }))
                return False

            # AC: Determinar file_type (pdf o txt)
            file_type = document.file_type.lower()
            file_path = document.file_path

            logger.info(json.dumps({
                "event": "extraction_started",
                "document_id": document_id,
                "file_type": file_type,
                "file_path": file_path,
                "timestamp": datetime.now().isoformat()
            }))

            # AC: Llamar función extractora apropiada
            extracted_text: Optional[str] = None

            if file_type == 'pdf':
                extracted_text = extract_text_from_pdf(file_path)
            elif file_type == 'txt':
                extracted_text = extract_text_from_txt(file_path)
            else:
                error_msg = f"Tipo de archivo no soportado: {file_type}"
                logger.error(json.dumps({
                    "event": "extraction_error",
                    "document_id": document_id,
                    "file_type": file_type,
                    "error": error_msg,
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }))
                return False

            # AC: Actualizar Document.content_text, is_indexed=True, indexed_at=now()
            document.content_text = extracted_text
            document.is_indexed = True
            document.indexed_at = datetime.now(timezone.utc)

            db.add(document)
            db.commit()
            db.refresh(document)

            # AC6: Logging estructurado (tiempo, éxito/error)
            extraction_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(json.dumps({
                "event": "extraction_completed",
                "document_id": document_id,
                "file_type": file_type,
                "text_length": len(extracted_text) if extracted_text else 0,
                "extraction_time_ms": round(extraction_time_ms, 2),
                "success": True,
                "timestamp": datetime.now().isoformat()
            }))

            return True

        except FileNotFoundError as e:
            # AC5: Manejo de errores - archivo no encontrado
            extraction_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Archivo no encontrado: {str(e)}"

            logger.error(json.dumps({
                "event": "extraction_error",
                "document_id": document_id,
                "file_type": file_type if 'file_type' in locals() else "unknown",
                "error": error_msg,
                "extraction_time_ms": round(extraction_time_ms, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))

            # AC5: Marcar is_indexed=False para permitir reintento
            try:
                if 'document' in locals() and document:
                    document.is_indexed = False
                    db.add(document)
                    db.commit()
            except Exception as commit_error:
                logger.error(json.dumps({
                    "event": "rollback_error",
                    "document_id": document_id,
                    "error": str(commit_error),
                    "timestamp": datetime.now().isoformat()
                }))

            return False

        except ValueError as e:
            # AC5: Manejo de errores - PDF corrupto o sin texto
            extraction_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Error en extracción: {str(e)}"

            logger.error(json.dumps({
                "event": "extraction_error",
                "document_id": document_id,
                "file_type": file_type if 'file_type' in locals() else "unknown",
                "error": error_msg,
                "extraction_time_ms": round(extraction_time_ms, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))

            # AC5: Marcar is_indexed=False para permitir reintento
            try:
                if 'document' in locals() and document:
                    document.is_indexed = False
                    db.add(document)
                    db.commit()
            except Exception as commit_error:
                logger.error(json.dumps({
                    "event": "rollback_error",
                    "document_id": document_id,
                    "error": str(commit_error),
                    "timestamp": datetime.now().isoformat()
                }))

            return False

        except Exception as e:
            # AC5: Manejo de errores genéricos
            extraction_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Error inesperado: {str(e)}"

            logger.error(json.dumps({
                "event": "extraction_error",
                "document_id": document_id,
                "file_type": file_type if 'file_type' in locals() else "unknown",
                "error": error_msg,
                "extraction_time_ms": round(extraction_time_ms, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))

            # AC5: Manejo de errores con rollback
            try:
                db.rollback()
                if 'document' in locals() and document:
                    document.is_indexed = False
                    db.add(document)
                    db.commit()
            except Exception as rollback_error:
                logger.error(json.dumps({
                    "event": "rollback_error",
                    "document_id": document_id,
                    "error": str(rollback_error),
                    "timestamp": datetime.now().isoformat()
                }))

            return False

    @staticmethod
    async def get_documents(
        db: Session,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "upload_date",
        order: str = "desc"
    ) -> List[DocumentResponse]:
        """
        Obtiene lista de documentos con filtros, paginación y ordenamiento.

        Args:
            db: Sesión de base de datos SQLModel
            category: Filtro opcional por categoría
            limit: Límite de resultados (default: 20)
            offset: Offset para paginación (default: 0)
            sort_by: Campo de ordenamiento (upload_date, title, file_size_bytes)
            order: Dirección de ordenamiento (asc, desc)

        Returns:
            List[DocumentResponse]: Lista de documentos con uploaded_by como username

        Example:
            >>> async with get_session() as db:
            >>>     docs = await DocumentService.get_documents(db, category="manual", limit=10)
            >>>     assert len(docs) <= 10
        """
        start_time = datetime.now()

        try:
            # Validar campos de ordenamiento permitidos
            allowed_sort_fields = {"upload_date", "title", "file_size_bytes"}
            if sort_by not in allowed_sort_fields:
                raise ValueError(f"Campo de ordenamiento no permitido: {sort_by}")

            # Validar dirección de ordenamiento
            if order not in {"asc", "desc"}:
                raise ValueError(f"Dirección de ordenamiento no permitida: {order}")

            # Construir query base con JOIN para obtener username
            query = (
                select(Document, User.username)
                .join(User, Document.uploaded_by == User.id)
                .where(User.is_active == True)  # Solo usuarios activos
            )

            # Aplicar filtro por categoría si se proporciona
            if category:
                query = query.where(Document.category == category)

            # Aplicar ordenamiento
            sort_column = getattr(Document, sort_by)
            if order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

            # Aplicar paginación
            query = query.offset(offset).limit(limit)

            # Ejecutar query
            results = db.exec(query).all()

            # Convertir resultados a DocumentResponse
            documents = []
            for document, username in results:
                doc_response = DocumentResponse(
                    id=document.id,
                    title=document.title,
                    description=document.description,
                    category=document.category,
                    file_type=document.file_type,
                    file_size_bytes=document.file_size_bytes,
                    upload_date=document.upload_date,
                    uploaded_by=username,  # Username en lugar de user_id
                    is_indexed=document.is_indexed,
                    indexed_at=document.indexed_at
                )
                documents.append(doc_response)

            # Logging estructurado
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(json.dumps({
                "event": "documents_listed",
                "category": category,
                "limit": limit,
                "offset": offset,
                "sort_by": sort_by,
                "order": order,
                "results_count": len(documents),
                "query_time_ms": round(query_time_ms, 2),
                "success": True,
                "timestamp": datetime.now().isoformat()
            }))

            return documents

        except ValueError as e:
            # Error de validación de parámetros
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.error(json.dumps({
                "event": "documents_list_error",
                "category": category,
                "limit": limit,
                "offset": offset,
                "sort_by": sort_by,
                "order": order,
                "error": str(e),
                "query_time_ms": round(query_time_ms, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))

            raise  # Re-raise ValueError para que el controller maneje el 400

        except Exception as e:
            # Error genérico
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.error(json.dumps({
                "event": "documents_list_error",
                "category": category,
                "limit": limit,
                "offset": offset,
                "sort_by": sort_by,
                "order": order,
                "error": str(e),
                "query_time_ms": round(query_time_ms, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))

            raise  # Re-raise para que el controller maneje el 500

    @staticmethod
    async def get_document_by_id(document_id: int, db: Session) -> Optional[DocumentResponse]:
        """
        Obtiene un documento por su ID con uploaded_by como username.

        Args:
            document_id: ID del documento a buscar
            db: Sesión de base de datos SQLModel

        Returns:
            Optional[DocumentResponse]: Documento encontrado o None

        Example:
            >>> async with get_session() as db:
            >>>     doc = await DocumentService.get_document_by_id(123, db)
            >>>     if doc:
            >>>         print(f"Documento: {doc.title}")
        """
        start_time = datetime.now()

        try:
            # Query con JOIN para obtener username
            query = (
                select(Document, User.username)
                .join(User, Document.uploaded_by == User.id)
                .where(Document.id == document_id)
                .where(User.is_active == True)
            )

            result = db.exec(query).first()

            if not result:
                logger.info(json.dumps({
                    "event": "document_not_found",
                    "document_id": document_id,
                    "query_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2),
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                }))
                return None

            document, username = result

            doc_response = DocumentResponse(
                id=document.id,
                title=document.title,
                description=document.description,
                category=document.category,
                file_type=document.file_type,
                file_size_bytes=document.file_size_bytes,
                upload_date=document.upload_date,
                uploaded_by=username,
                is_indexed=document.is_indexed,
                indexed_at=document.indexed_at
            )

            # Logging estructurado
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(json.dumps({
                "event": "document_retrieved",
                "document_id": document_id,
                "title": document.title,
                "category": document.category,
                "query_time_ms": round(query_time_ms, 2),
                "success": True,
                "timestamp": datetime.now().isoformat()
            }))

            return doc_response

        except Exception as e:
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.error(json.dumps({
                "event": "document_retrieval_error",
                "document_id": document_id,
                "error": str(e),
                "query_time_ms": round(query_time_ms, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))

            raise  # Re-raise para que el controller maneje el 500

    @staticmethod
    async def get_categories(db: Session) -> List[CategoryResponse]:
        """
        Obtiene lista de categorías con contador de documentos.

        Args:
            db: Sesión de base de datos SQLModel

        Returns:
            List[CategoryResponse]: Lista de categorías con document_count

        Example:
            >>> async with get_session() as db:
            >>>     categories = await DocumentService.get_categories(db)
            >>>     for cat in categories:
            >>>         print(f"{cat.name}: {cat.document_count} documentos")
        """
        start_time = datetime.now()

        try:
            # Query para obtener categorías con COUNT de documentos
            query = (
                select(
                    DocumentCategory.name,
                    DocumentCategory.description,
                    func.count(Document.id).label("document_count")
                )
                .outerjoin(Document, DocumentCategory.name == Document.category)
                .group_by(DocumentCategory.name, DocumentCategory.description)
                .order_by(DocumentCategory.name)
            )

            results = db.exec(query).all()

            # Convertir resultados a CategoryResponse
            categories = []
            for category_name, description, document_count in results:
                category_response = CategoryResponse(
                    name=category_name,
                    description=description,
                    document_count=document_count or 0
                )
                categories.append(category_response)

            # Logging estructurado
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(json.dumps({
                "event": "categories_listed",
                "categories_count": len(categories),
                "total_documents": sum(cat.document_count for cat in categories),
                "query_time_ms": round(query_time_ms, 2),
                "success": True,
                "timestamp": datetime.now().isoformat()
            }))

            return categories

        except Exception as e:
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.error(json.dumps({
                "event": "categories_list_error",
                "error": str(e),
                "query_time_ms": round(query_time_ms, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))

            raise  # Re-raise para que el controller maneje el 500