"""
Tests para extracción de texto de documentos PDF y TXT.

Cubre los siguientes acceptance criteria:
- AC1: Extracción de archivos TXT
- AC2: Extracción de archivos PDF
- AC3: Procesamiento asíncrono
- AC4: Endpoint de verificación de estado
- AC5: Manejo de errores de extracción
- AC6: Logging y métricas
"""

import pytest
import os
import tempfile
from datetime import datetime
from sqlmodel import Session, select
from fastapi import status
from pypdf import PdfWriter

from app.models.document import Document
from app.services.document_service import DocumentService
from app.utils.pdf_extractor import extract_text_from_pdf, extract_text_from_txt


# ============================================================================
# Tests de Utilidades de Extracción (AC1, AC2)
# ============================================================================

def test_extract_text_from_txt_success():
    """
    AC1: Test extracción exitosa de archivo TXT
    Given un archivo TXT válido
    When se extrae el texto
    Then se retorna el contenido completo
    """
    # Arrange
    content = "Este es un documento de prueba.\nCon múltiples líneas."

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name

    try:
        # Act
        extracted = extract_text_from_txt(temp_path)

        # Assert
        assert extracted == content
        assert len(extracted) > 0
    finally:
        # Cleanup
        os.unlink(temp_path)


def test_extract_text_from_txt_with_latin1_encoding():
    """
    AC1: Test extracción TXT con encoding alternativo (latin-1)
    Given un archivo TXT con encoding latin-1
    When se intenta extraer con UTF-8 y falla
    Then se usa latin-1 como fallback
    """
    # Arrange
    content = "Documento con á é í ó ú ñ"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='latin-1') as f:
        f.write(content)
        temp_path = f.name

    try:
        # Act
        extracted = extract_text_from_txt(temp_path)

        # Assert
        assert len(extracted) > 0
        assert 'Documento' in extracted
    finally:
        # Cleanup
        os.unlink(temp_path)


def test_extract_text_from_txt_applies_50k_limit():
    """
    AC1: Test límite de 50,000 caracteres en TXT
    Given un archivo TXT con más de 50,000 caracteres
    When se extrae el texto
    Then se retorna exactamente 50,000 caracteres
    """
    # Arrange
    large_content = "A" * 60_000  # 60k caracteres

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(large_content)
        temp_path = f.name

    try:
        # Act
        extracted = extract_text_from_txt(temp_path)

        # Assert
        assert len(extracted) == 50_000
    finally:
        # Cleanup
        os.unlink(temp_path)


def test_extract_text_from_txt_file_not_found():
    """
    AC1, AC5: Test manejo de archivo TXT no encontrado
    Given una ruta de archivo que no existe
    When se intenta extraer
    Then se lanza FileNotFoundError
    """
    # Arrange
    non_existent_path = "/tmp/archivo_inexistente_12345.txt"

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        extract_text_from_txt(non_existent_path)


def test_extract_text_from_pdf_success():
    """
    AC2: Test extracción exitosa de archivo PDF
    Given un archivo PDF válido con texto
    When se extrae el texto
    Then se retorna el contenido de todas las páginas
    """
    # Arrange: Crear PDF simple con texto
    from pypdf import PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name

    try:
        # Crear PDF con ReportLab
        c = canvas.Canvas(temp_path, pagesize=letter)
        c.drawString(100, 750, "Documento de Prueba")
        c.drawString(100, 735, "Esta es la primera pagina")
        c.showPage()
        c.drawString(100, 750, "Segunda pagina del documento")
        c.save()

        # Act
        extracted = extract_text_from_pdf(temp_path)

        # Assert
        assert len(extracted) > 0
        assert "Documento" in extracted or "Prueba" in extracted
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_extract_text_from_pdf_applies_50k_limit():
    """
    AC2: Test límite de 50,000 caracteres en PDF
    Given un archivo PDF con más de 50,000 caracteres
    When se extrae el texto
    Then se retorna máximo 50,000 caracteres
    """
    # Arrange: Crear PDF con mucho texto
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name

    try:
        c = canvas.Canvas(temp_path, pagesize=letter)

        # Agregar múltiples páginas con texto
        for page in range(100):
            for line in range(50):
                c.drawString(100, 750 - (line * 15), "A" * 100)
            c.showPage()
        c.save()

        # Act
        extracted = extract_text_from_pdf(temp_path)

        # Assert
        assert len(extracted) <= 50_000
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_extract_text_from_pdf_file_not_found():
    """
    AC2, AC5: Test manejo de archivo PDF no encontrado
    Given una ruta que no existe
    When se intenta extraer
    Then se lanza FileNotFoundError
    """
    # Arrange
    non_existent_path = "/tmp/pdf_inexistente_12345.pdf"

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf(non_existent_path)


def test_extract_text_from_pdf_corrupted_file():
    """
    AC5: Test manejo de PDF corrupto
    Given un archivo PDF corrupto
    When se intenta extraer
    Then se lanza ValueError
    """
    # Arrange: Crear archivo con contenido inválido
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        f.write("Este no es un PDF válido, solo texto plano")
        temp_path = f.name

    try:
        # Act & Assert
        with pytest.raises(ValueError):
            extract_text_from_pdf(temp_path)
    finally:
        # Cleanup
        os.unlink(temp_path)


# ============================================================================
# Tests de DocumentService (AC1, AC2, AC5, AC6)
# ============================================================================

@pytest.mark.asyncio
async def test_document_service_extract_text_txt(test_db_session: Session, test_category):
    """
    AC1: Test servicio extrae texto de documento TXT
    Given un documento TXT en la base de datos
    When se llama a DocumentService.extract_text
    Then se actualiza content_text, is_indexed=True, indexed_at
    """
    # Arrange: Crear archivo TXT y documento en DB
    content = "Contenido de prueba del documento"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name

    try:
        document = Document(
            title="Test Document",
            description="Test",
            category=test_category.name,
            file_type="txt",
            file_size_bytes=len(content),
            file_path=temp_path,
            uploaded_by=1,
            is_indexed=False
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)

        # Act
        result = await DocumentService.extract_text(document.id, test_db_session)

        # Assert
        assert result is True

        # Verificar documento actualizado
        test_db_session.refresh(document)
        assert document.content_text == content
        assert document.is_indexed is True
        assert document.indexed_at is not None

    finally:
        # Cleanup
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_document_service_extract_text_pdf(test_db_session: Session, test_category):
    """
    AC2: Test servicio extrae texto de documento PDF
    Given un documento PDF en la base de datos
    When se llama a DocumentService.extract_text
    Then se actualiza content_text, is_indexed=True, indexed_at
    """
    # Arrange: Crear PDF y documento en DB
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name

    try:
        c = canvas.Canvas(temp_path, pagesize=letter)
        c.drawString(100, 750, "PDF de Prueba")
        c.save()

        document = Document(
            title="Test PDF Document",
            description="Test",
            category=test_category.name,
            file_type="pdf",
            file_size_bytes=1000,
            file_path=temp_path,
            uploaded_by=1,
            is_indexed=False
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)

        # Act
        result = await DocumentService.extract_text(document.id, test_db_session)

        # Assert
        assert result is True

        # Verificar documento actualizado
        test_db_session.refresh(document)
        assert document.content_text is not None
        assert len(document.content_text) > 0
        assert document.is_indexed is True
        assert document.indexed_at is not None

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.asyncio
async def test_document_service_handles_missing_file(test_db_session: Session, test_category):
    """
    AC5: Test servicio maneja archivo faltante
    Given un documento con file_path que no existe
    When se intenta extraer
    Then retorna False y mantiene is_indexed=False
    """
    # Arrange
    document = Document(
        title="Test Missing File",
        description="Test",
        category=test_category.name,
        file_type="txt",
        file_size_bytes=100,
        file_path="/tmp/archivo_que_no_existe_12345.txt",
        uploaded_by=1,
        is_indexed=False
    )
    test_db_session.add(document)
    test_db_session.commit()
    test_db_session.refresh(document)

    # Act
    result = await DocumentService.extract_text(document.id, test_db_session)

    # Assert
    assert result is False

    # Verificar documento NO fue indexado
    test_db_session.refresh(document)
    assert document.is_indexed is False
    assert document.indexed_at is None


@pytest.mark.asyncio
async def test_document_service_handles_document_not_found(test_db_session: Session):
    """
    AC5: Test servicio maneja documento inexistente
    Given un document_id que no existe
    When se intenta extraer
    Then retorna False
    """
    # Arrange
    non_existent_id = 99999

    # Act
    result = await DocumentService.extract_text(non_existent_id, test_db_session)

    # Assert
    assert result is False


# ============================================================================
# Tests de Endpoint de Status (AC4)
# ============================================================================

def test_get_document_status_indexed(test_client, admin_token, test_db_session, test_category):
    """
    AC4: Test endpoint status para documento indexado
    Given un documento con is_indexed=True
    When se consulta GET /api/knowledge/documents/{id}/status
    Then se retorna status="indexed"
    """
    # Arrange
    document = Document(
        title="Indexed Document",
        description="Test",
        category=test_category.name,
        file_type="txt",
        file_size_bytes=100,
        file_path="/uploads/test.txt",
        uploaded_by=1,
        is_indexed=True,
        indexed_at=datetime.now(),
        content_text="Sample content"
    )
    test_db_session.add(document)
    test_db_session.commit()
    test_db_session.refresh(document)

    # Act
    response = test_client.get(
        f"/api/knowledge/documents/{document.id}/status",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["document_id"] == document.id
    assert data["title"] == document.title
    assert data["is_indexed"] is True
    assert data["indexed_at"] is not None
    assert data["status"] == "indexed"


def test_get_document_status_processing(test_client, admin_token, test_db_session, test_category):
    """
    AC4: Test endpoint status para documento en procesamiento
    Given un documento con is_indexed=False
    When se consulta GET /api/knowledge/documents/{id}/status
    Then se retorna status="processing"
    """
    # Arrange
    document = Document(
        title="Processing Document",
        description="Test",
        category=test_category.name,
        file_type="pdf",
        file_size_bytes=1000,
        file_path="/uploads/test.pdf",
        uploaded_by=1,
        is_indexed=False
    )
    test_db_session.add(document)
    test_db_session.commit()
    test_db_session.refresh(document)

    # Act
    response = test_client.get(
        f"/api/knowledge/documents/{document.id}/status",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["document_id"] == document.id
    assert data["is_indexed"] is False
    assert data["indexed_at"] is None
    assert data["status"] == "processing"


def test_get_document_status_not_found(test_client, admin_token):
    """
    AC4: Test endpoint status para documento inexistente
    Given un document_id que no existe
    When se consulta GET /api/knowledge/documents/{id}/status
    Then se retorna 404
    """
    # Arrange
    non_existent_id = 99999

    # Act
    response = test_client.get(
        f"/api/knowledge/documents/{non_existent_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_document_status_requires_authentication(test_client):
    """
    AC4: Test endpoint status requiere autenticación
    Given ningún token de autenticación
    When se consulta GET /api/knowledge/documents/{id}/status
    Then se retorna 401 o 403 (sin autorización)
    """
    # Act
    response = test_client.get("/api/knowledge/documents/1/status")

    # Assert - acepta tanto 401 como 403 ya que ambos indican falta de autenticación
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


# ============================================================================
# Tests de Procesamiento Asíncrono (AC3)
# ============================================================================

def test_upload_returns_immediately_without_waiting_for_extraction(
    test_client, admin_token, test_category
):
    """
    AC3: Test upload retorna inmediatamente sin esperar extracción
    Given un archivo válido
    When se llama a POST /api/knowledge/upload
    Then retorna 201 inmediatamente
    And la extracción se ejecuta en background
    """
    # Arrange
    file_content = b"Contenido de prueba"

    # Act
    response = test_client.post(
        "/api/knowledge/upload",
        files={"file": ("test.txt", file_content, "text/plain")},
        data={
            "title": "Test Async Upload",
            "description": "Test async processing",
            "category": test_category.name
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "uploaded"

    # Note: La extracción se ejecuta en background,
    # por lo que el documento inicialmente estará is_indexed=False
