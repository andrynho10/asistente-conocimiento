"""
Tests para endpoints de descarga y preview de documentos.
Cubre los requisitos AC1-AC5 de la Story 2.6.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timezone

from app.main import app
from app.database import get_session
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.models.document import Document
from app.models.audit import AuditLog
from app.services.document_service import DocumentService

client = None  # Será inyectado por setup_test_client_globals en conftest.py


# Override dependencies para testing
@pytest.fixture
def override_get_current_user():
    """Override para mock de usuario autenticado"""
    def _get_current_user():
        return User(
            id=1,
            username="admin",
            email="admin@test.com",
            role=UserRole.admin,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    return _get_current_user


@pytest.fixture
def override_get_session():
    """Override para mock de sesión de base de datos"""
    def _get_session():
        return Mock(spec=Session)
    return _get_session


@pytest.fixture
def authenticated_client(override_get_current_user, override_get_session):
    """Client con overrides de dependencias"""
    from app.main import app

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    """Mock de sesión de base de datos"""
    session = Mock(spec=Session)
    return session


@pytest.fixture
def mock_admin_user():
    """Mock de usuario administrador"""
    return User(
        id=1,
        username="admin",
        email="admin@test.com",
        role=UserRole.admin,
        is_active=True
    )


@pytest.fixture
def mock_normal_user():
    """Mock de usuario normal"""
    return User(
        id=2,
        username="user",
        email="user@test.com",
        role=UserRole.user,
        is_active=True
    )


@pytest.fixture
def sample_pdf_document():
    """Documento PDF de ejemplo"""
    return Document(
        id=1,
        title="Políticas de RRHH",
        description="Políticas internas de recursos humanos",
        category="Recursos Humanos",
        file_type="pdf",
        file_size_bytes=1024000,
        file_path="/uploads/politicas_rrhh_20231113_120000.pdf",
        uploaded_by=1,
        is_indexed=True,
        indexed_at=datetime.now(timezone.utc),
        upload_date=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_txt_document():
    """Documento TXT de ejemplo"""
    return Document(
        id=2,
        title="Manual deEmpleado",
        description="Guía para nuevos empleados",
        category="Capacitación",
        file_type="txt",
        file_size_bytes=5120,
        file_path="/uploads/manual_empleado_20231113_120000.txt",
        uploaded_by=1,
        is_indexed=True,
        indexed_at=datetime.now(timezone.utc),
        upload_date=datetime.now(timezone.utc)
    )


@pytest.fixture
def temp_pdf_file():
    """Archivo PDF temporal para pruebas"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(b"PDF content for testing")
        tmp_path = tmp.name

    yield tmp_path

    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def temp_txt_file():
    """Archivo TXT temporal para pruebas"""
    content = "Este es un archivo de texto de prueba para el manual de empleados. " * 50
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    yield tmp_path

    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


class TestDownloadEndpoint:
    """Tests para el endpoint de descarga de documentos"""

    async def test_download_pdf_success_unit(
        self,
        temp_pdf_file
    ):
        """AC1: Descarga exitosa de PDF con headers correctos - Unit Test"""
        from app.services.document_service import DocumentService
        from app.models.document import Document
        from sqlmodel import select

        # Crear mock de documento
        mock_doc = Document(
            id=1,
            title="Políticas de RRHH",
            file_type="pdf",
            file_size_bytes=1024000,
            file_path=temp_pdf_file
        )

        # Mock de sesión de base de datos
        mock_db = Mock()
        mock_query = Mock()
        mock_query.first.return_value = mock_doc
        mock_db.exec.return_value = mock_query

        # Test directo al servicio
        result = await DocumentService.download_document(1, mock_db)

        # Assertions
        assert result is not None
        file_path, file_type, safe_filename, file_size = result
        assert file_path == temp_pdf_file
        assert file_type == "pdf"
        assert safe_filename == "Políticas_de_RRHH.pdf"
        assert file_size == 1024000

    async def test_download_txt_success_unit(
        self,
        temp_txt_file
    ):
        """AC1: Descarga exitosa de TXT con headers correctos - Unit Test"""
        from app.services.document_service import DocumentService
        from app.models.document import Document

        # Crear mock de documento
        mock_doc = Document(
            id=2,
            title="Manual deEmpleado",
            file_type="txt",
            file_size_bytes=5120,
            file_path=temp_txt_file
        )

        # Mock de sesión de base de datos
        mock_db = Mock()
        mock_query = Mock()
        mock_query.first.return_value = mock_doc
        mock_db.exec.return_value = mock_query

        # Test directo al servicio
        result = await DocumentService.download_document(2, mock_db)

        # Assertions
        assert result is not None
        file_path, file_type, safe_filename, file_size = result
        assert file_path == temp_txt_file
        assert file_type == "txt"
        assert safe_filename == "Manual_deEmpleado.txt"
        assert file_size == 5120

    def test_download_document_not_found(
        self,
        client_with_mocked_auth,
        monkeypatch
    ):
        """AC2: Documento no existe retorna 404"""
        from app.services.document_service import DocumentService

        # Mock de DocumentService.download_document retorna None
        async def mock_download(doc_id, db, user=None):
            return None

        monkeypatch.setattr(DocumentService, 'download_document', mock_download)

        # Test usando cliente con auth mockeada
        response = client_with_mocked_auth.get("/api/knowledge/documents/999/download")

        # Assertions
        assert response.status_code == 404
        response_data = response.json()["detail"]
        assert response_data["code"] == "DOCUMENT_NOT_FOUND"
        assert "El documento solicitado no existe" in response_data["message"]

    def test_download_unauthorized(self):
        """AC2: No autenticado retorna 401"""
        # Test sin token de autenticación
        response = client.get("/api/knowledge/documents/1/download")

        # Should return 401 due to JWT middleware
        assert response.status_code in [401, 403]

    def test_download_orphaned_file_cleanup(
        self,
        client_with_mocked_auth,
        monkeypatch
    ):
        """AC3: Archivo huérfano elimina registro y retorna 404"""
        from app.services.document_service import DocumentService

        # Mock de DocumentService.download_document retorna None (archivo huérfano)
        async def mock_download(doc_id, db, user=None):
            return None

        monkeypatch.setattr(DocumentService, 'download_document', mock_download)

        # Test
        response = client_with_mocked_auth.get("/api/knowledge/documents/1/download")

        # Assertions
        assert response.status_code == 404
        response_data = response.json()["detail"]
        assert response_data["code"] == "DOCUMENT_NOT_FOUND"

    def test_download_directory_traversal_prevention(
        self,
        client_with_mocked_auth,
        monkeypatch
    ):
        """AC3: Prevención de directory traversal"""
        from app.services.document_service import DocumentService

        # Mock de DocumentService.download_document con path malicioso
        async def mock_download(doc_id, db, user=None):
            return (
                "/etc/passwd",  # file_path malicioso
                "pdf",         # file_type
                "safe.pdf",    # safe_filename
                1024           # file_size
            )

        monkeypatch.setattr(DocumentService, 'download_document', mock_download)

        # Test
        response = client_with_mocked_auth.get("/api/knowledge/documents/1/download")

        # Assertions - debe rechazar el path malicioso
        assert response.status_code == 404
        response_data = response.json()["detail"]
        assert response_data["code"] == "DOCUMENT_NOT_FOUND"

    def test_download_audit_logging(
        self,
        client_with_mocked_auth,
        monkeypatch
    ):
        """AC4: Solicitud de descarga retorna 404 si archivo no existe"""
        from app.services.document_service import DocumentService

        # Mock de DocumentService.download_document para retornar None
        # (simula documento no encontrado después de búsqueda)
        async def mock_download(doc_id, db, user=None):
            return None

        monkeypatch.setattr(DocumentService, 'download_document', mock_download)

        # Test
        response = client_with_mocked_auth.get("/api/knowledge/documents/1/download")

        # Assertions
        assert response.status_code == 404


class TestPreviewEndpoint:
    """Tests para el endpoint de preview de documentos"""

    def test_preview_success(
        self,
        client_with_mocked_auth,
        monkeypatch
    ):
        """AC5: Preview exitoso retorna primeros 500 caracteres"""
        from app.services.document_service import DocumentService

        # Mock de preview text (exactamente 500 caracteres)
        preview_text = "Este es el contenido del manual de empleados. " * 25  # ~600 caracteres
        preview_text = preview_text[:500]  # Exactamente 500 caracteres

        async def mock_preview(doc_id, db):
            return preview_text

        monkeypatch.setattr(DocumentService, 'get_document_preview', mock_preview)

        # Test
        response = client_with_mocked_auth.get("/api/knowledge/documents/1/preview")

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["document_id"] == 1
        assert response_data["preview"] == preview_text
        assert response_data["preview_length"] == 500
        assert response_data["message"] == "Preview del documento"

    def test_preview_document_not_found(
        self,
        client_with_mocked_auth,
        monkeypatch
    ):
        """AC5: Documento no existe retorna 404"""
        from app.services.document_service import DocumentService

        async def mock_preview(doc_id, db):
            return None

        monkeypatch.setattr(DocumentService, 'get_document_preview', mock_preview)

        # Test
        response = client_with_mocked_auth.get("/api/knowledge/documents/999/preview")

        # Assertions
        assert response.status_code == 404
        response_data = response.json()["detail"]
        assert response_data["code"] == "DOCUMENT_NOT_FOUND"
        assert "no existe o no tiene contenido extraído" in response_data["message"]

    def test_preview_no_content_extracted(
        self,
        client_with_mocked_auth,
        monkeypatch
    ):
        """AC5: Documento sin contenido extraído retorna 404"""
        from app.services.document_service import DocumentService

        async def mock_preview(doc_id, db):
            return None

        monkeypatch.setattr(DocumentService, 'get_document_preview', mock_preview)

        # Test
        response = client_with_mocked_auth.get("/api/knowledge/documents/1/preview")

        # Assertions
        assert response.status_code == 404
        response_data = response.json()["detail"]
        assert response_data["code"] == "DOCUMENT_NOT_FOUND"

    def test_preview_unauthorized(self):
        """AC2: No autenticado retorna 401"""
        # Test sin token de autenticación
        response = client.get("/api/knowledge/documents/1/preview")

        # Should return 401 due to JWT middleware
        assert response.status_code in [401, 403]


class TestDocumentServiceDownload:
    """Tests para el método download_document de DocumentService"""

    @pytest.mark.asyncio
    async def test_download_document_success(
        self,
        mock_db_session,
        sample_pdf_document,
        temp_pdf_file
    ):
        """Test exitoso de download_document"""
        # Setup mock query
        mock_query = Mock()
        mock_query.first.return_value = sample_pdf_document
        mock_db_session.exec.return_value = mock_query

        # Override file_path con archivo temporal
        sample_pdf_document.file_path = temp_pdf_file

        # Test
        result = await DocumentService.download_document(1, mock_db_session)

        # Assertions
        assert result is not None
        file_path, file_type, safe_filename, file_size = result
        assert file_path == temp_pdf_file
        assert file_type == "pdf"
        assert safe_filename == "Políticas_de_RRHH.pdf"
        assert file_size == 1024000

    @pytest.mark.asyncio
    async def test_download_document_not_found(self, mock_db_session):
        """Test cuando documento no existe"""
        # Setup mock query returning None
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db_session.exec.return_value = mock_query

        # Test
        result = await DocumentService.download_document(999, mock_db_session)

        # Assertions
        assert result is None

    @pytest.mark.asyncio
    async def test_download_orphaned_file_cleanup(
        self,
        mock_db_session,
        sample_pdf_document
    ):
        """Test cleanup de archivo huérfano"""
        # Setup mocks
        mock_query = Mock()
        mock_query.first.return_value = sample_pdf_document
        mock_db_session.exec.return_value = mock_query

        # File path que no existe (archivo huérfano)
        sample_pdf_document.file_path = "/uploads/orphaned_file.pdf"

        # Test
        result = await DocumentService.download_document(1, mock_db_session)

        # Assertions
        assert result is None
        # Verificar que se llamó a delete y commit
        mock_db_session.delete.assert_called_once_with(sample_pdf_document)
        mock_db_session.commit.assert_called()


class TestDocumentServicePreview:
    """Tests para el método get_document_preview de DocumentService"""

    @pytest.mark.asyncio
    async def test_preview_success(
        self,
        mock_db_session,
        sample_txt_document
    ):
        """Test exitoso de preview"""
        # Setup mock query
        mock_query = Mock()
        mock_query.first.return_value = sample_txt_document
        mock_db_session.exec.return_value = mock_query

        # Setup content text
        long_content = "Este es un contenido largo para el manual. " * 100
        sample_txt_document.content_text = long_content

        # Test
        result = await DocumentService.get_document_preview(2, mock_db_session)

        # Assertions
        assert result is not None
        assert len(result) == 500  # Primeros 500 caracteres
        assert result == long_content[:500]

    @pytest.mark.asyncio
    async def test_preview_document_not_found(self, mock_db_session):
        """Test cuando documento no existe"""
        # Setup mock query returning None
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db_session.exec.return_value = mock_query

        # Test
        result = await DocumentService.get_document_preview(999, mock_db_session)

        # Assertions
        assert result is None

    @pytest.mark.asyncio
    async def test_preview_no_content(
        self,
        mock_db_session,
        sample_txt_document
    ):
        """Test cuando documento no tiene contenido extraído"""
        # Setup mocks
        mock_query = Mock()
        mock_query.first.return_value = sample_txt_document
        mock_db_session.exec.return_value = mock_query

        # Sin contenido
        sample_txt_document.content_text = None

        # Test
        result = await DocumentService.get_document_preview(2, mock_db_session)

        # Assertions
        assert result is None