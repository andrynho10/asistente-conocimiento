"""
Servicio para gestión y procesamiento de documentos.

Orquesta la extracción de texto de documentos cargados y actualiza
el estado de indexación en la base de datos.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session, select

from app.models.document import Document
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
