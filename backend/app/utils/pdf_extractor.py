"""
Utilidades para extracción de texto de documentos PDF y TXT.

Este módulo provee funciones puras para extraer texto de archivos PDF y TXT,
con manejo robusto de errores y normalización de contenido.
"""

import logging
import json
from typing import Optional
from pypdf import PdfReader
from datetime import datetime

# Configurar logging estructurado
logger = logging.getLogger(__name__)

# Límite de caracteres según AC2
MAX_TEXT_LENGTH = 50_000


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrae texto de un archivo PDF usando PyPDF.

    Args:
        file_path: Ruta completa al archivo PDF

    Returns:
        str: Texto extraído concatenado de todas las páginas,
             normalizado y limitado a 50,000 caracteres

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el PDF está corrupto o no se puede leer
        Exception: Para otros errores de lectura

    Example:
        >>> text = extract_text_from_pdf("/uploads/manual_20251112.pdf")
        >>> assert len(text) <= 50000
    """
    start_time = datetime.now()

    try:
        # Abrir PDF con PyPDF
        reader = PdfReader(file_path)

        # Verificar que tenga páginas
        if len(reader.pages) == 0:
            error_msg = f"PDF vacío: {file_path}"
            logger.error(json.dumps({
                "event": "pdf_extraction_error",
                "file_path": file_path,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }))
            raise ValueError(error_msg)

        # Extraer texto de todas las páginas
        text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                # Log error pero continúa con otras páginas
                logger.warning(json.dumps({
                    "event": "pdf_page_extraction_warning",
                    "file_path": file_path,
                    "page_num": page_num,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
                continue

        # Concatenar todo el texto
        full_text = "\n".join(text_parts)

        # Normalizar espacios y saltos de línea
        full_text = _normalize_text(full_text)

        # Limitar a 50,000 caracteres (AC2)
        if len(full_text) > MAX_TEXT_LENGTH:
            full_text = full_text[:MAX_TEXT_LENGTH]
            logger.info(json.dumps({
                "event": "text_truncated",
                "file_path": file_path,
                "original_length": len(full_text),
                "truncated_length": MAX_TEXT_LENGTH
            }))

        # Log exitoso con métricas (AC6)
        extraction_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(json.dumps({
            "event": "pdf_extraction_success",
            "file_path": file_path,
            "file_type": "pdf",
            "text_length": len(full_text),
            "pages_extracted": len(text_parts),
            "extraction_time_ms": round(extraction_time_ms, 2),
            "success": True,
            "timestamp": datetime.now().isoformat()
        }))

        return full_text

    except FileNotFoundError:
        error_msg = f"Archivo no encontrado: {file_path}"
        logger.error(json.dumps({
            "event": "pdf_extraction_error",
            "file_path": file_path,
            "error": error_msg,
            "success": False,
            "timestamp": datetime.now().isoformat()
        }))
        raise FileNotFoundError(error_msg)

    except Exception as e:
        error_msg = f"Error extrayendo PDF: {str(e)}"
        extraction_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(json.dumps({
            "event": "pdf_extraction_error",
            "file_path": file_path,
            "file_type": "pdf",
            "error": error_msg,
            "extraction_time_ms": round(extraction_time_ms, 2),
            "success": False,
            "timestamp": datetime.now().isoformat()
        }))
        raise ValueError(error_msg) from e


def extract_text_from_txt(file_path: str) -> str:
    """
    Lee contenido de un archivo TXT con manejo de encoding.

    Intenta leer con UTF-8 primero, fallback a latin-1 si falla.

    Args:
        file_path: Ruta completa al archivo TXT

    Returns:
        str: Contenido del archivo limitado a 50,000 caracteres

    Raises:
        FileNotFoundError: Si el archivo no existe
        Exception: Si el archivo no se puede leer con ningún encoding

    Example:
        >>> text = extract_text_from_txt("/uploads/documento_20251112.txt")
        >>> assert isinstance(text, str)
    """
    start_time = datetime.now()
    encodings = ['utf-8', 'latin-1']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()

            # Limitar a 50,000 caracteres (AC1)
            if len(content) > MAX_TEXT_LENGTH:
                content = content[:MAX_TEXT_LENGTH]
                logger.info(json.dumps({
                    "event": "text_truncated",
                    "file_path": file_path,
                    "original_length": len(content),
                    "truncated_length": MAX_TEXT_LENGTH
                }))

            # Log exitoso con métricas (AC6)
            extraction_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(json.dumps({
                "event": "txt_extraction_success",
                "file_path": file_path,
                "file_type": "txt",
                "text_length": len(content),
                "encoding_used": encoding,
                "extraction_time_ms": round(extraction_time_ms, 2),
                "success": True,
                "timestamp": datetime.now().isoformat()
            }))

            return content

        except UnicodeDecodeError:
            # Probar siguiente encoding
            if encoding == encodings[-1]:
                # Último encoding falló
                error_msg = f"No se pudo decodificar archivo TXT con encodings: {encodings}"
                logger.error(json.dumps({
                    "event": "txt_extraction_error",
                    "file_path": file_path,
                    "error": error_msg,
                    "encodings_tried": encodings,
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }))
                raise Exception(error_msg)
            continue

        except FileNotFoundError:
            error_msg = f"Archivo no encontrado: {file_path}"
            logger.error(json.dumps({
                "event": "txt_extraction_error",
                "file_path": file_path,
                "error": error_msg,
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))
            raise FileNotFoundError(error_msg)

        except Exception as e:
            error_msg = f"Error leyendo archivo TXT: {str(e)}"
            extraction_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(json.dumps({
                "event": "txt_extraction_error",
                "file_path": file_path,
                "file_type": "txt",
                "error": error_msg,
                "extraction_time_ms": round(extraction_time_ms, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }))
            raise


def _normalize_text(text: str) -> str:
    """
    Normaliza texto: remueve espacios múltiples y normaliza saltos de línea.

    Args:
        text: Texto a normalizar

    Returns:
        str: Texto normalizado
    """
    import re

    # Normalizar saltos de línea (convertir CRLF y CR a LF)
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Reemplazar múltiples saltos de línea por máximo 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Reemplazar múltiples espacios por uno solo
    text = re.sub(r'[ \t]+', ' ', text)

    # Remover espacios al inicio/final de líneas
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    return text.strip()
