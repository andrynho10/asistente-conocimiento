"""
Tests de integración simplificados para endpoints de descarga.
Pruebas enfocadas en funcionalidad core y seguridad.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session
from datetime import datetime, timezone

from app.main import app
from app.database import get_session
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole


@pytest.fixture
def mock_db_session():
    """Mock de sesión de base de datos"""
    return Mock(spec=Session)


@pytest.fixture
def authenticated_user():
    """Usuario autenticado mock"""
    return User(
        id=1,
        username="admin",
        email="admin@test.com",
        role=UserRole.admin,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def normal_user():
    """Usuario normal mock"""
    return User(
        id=2,
        username="user",
        email="user@test.com",
        role=UserRole.user,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def authenticated_client(authenticated_user, mock_db_session):
    """Client con usuario autenticado"""
    app.dependency_overrides[get_current_user] = lambda: authenticated_user
    app.dependency_overrides[get_session] = lambda: mock_db_session

    with TestClient(app) as client:
        yield client

    # Limpiar overrides
    app.dependency_overrides.clear()


@pytest.fixture
def normal_client(normal_user, mock_db_session):
    """Client con usuario normal"""
    app.dependency_overrides[get_current_user] = lambda: normal_user
    app.dependency_overrides[get_session] = lambda: mock_db_session

    with TestClient(app) as client:
        yield client

    # Limpiar overrides
    app.dependency_overrides.clear()


@pytest.fixture
def temp_pdf_file():
    """Archivo PDF temporal"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n")
        tmp.flush()
        yield tmp.name
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def temp_txt_file():
    """Archivo TXT temporal"""
    content = "Contenido del manual de empleado para pruebas. " * 50
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write(content)
        tmp.flush()
        yield tmp.name
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


class TestDownloadEndpoint:
    """Tests básicos para endpoint de descarga"""

    @patch('app.routes.knowledge.DocumentService.download_document')
    @patch('app.routes.knowledge.os.path.abspath')
    def test_admin_download_pdf_success(
        self, mock_abspath, mock_download_service, authenticated_client, temp_pdf_file
    ):
        """AC1: Admin puede descargar PDF exitosamente"""
        # Setup
        mock_abspath.side_effect = lambda x: x
        mock_download_service.return_value = (
            temp_pdf_file, "pdf", "politicas_rrhh.pdf", 1024
        )

        # Test
        response = authenticated_client.get("/api/knowledge/documents/1/download")

        # Assertions
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "politicas_rrhh.pdf" in response.headers["content-disposition"]

    @patch('app.routes.knowledge.DocumentService.download_document')
    @patch('app.routes.knowledge.os.path.abspath')
    def test_user_download_txt_success(
        self, mock_abspath, mock_download_service, normal_client, temp_txt_file
    ):
        """AC1: Usuario normal puede descargar TXT exitosamente"""
        # Setup
        mock_abspath.side_effect = lambda x: x
        mock_download_service.return_value = (
            temp_txt_file, "txt", "manual_empleado.txt", 2048
        )

        # Test
        response = normal_client.get("/api/knowledge/documents/2/download")

        # Assertions
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain"
        assert "attachment" in response.headers["content-disposition"]
        assert "manual_empleado.txt" in response.headers["content-disposition"]

    @patch('app.routes.knowledge.DocumentService.download_document')
    def test_download_document_not_found(self, mock_download_service, authenticated_client):
        """AC2: Documento no existe retorna 404"""
        mock_download_service.return_value = None

        response = authenticated_client.get("/api/knowledge/documents/999/download")

        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "DOCUMENT_NOT_FOUND"

    def test_download_unauthorized(self):
        """AC2: No autenticado retorna 401/403"""
        client = TestClient(app)
        response = client.get("/api/knowledge/documents/1/download")
        assert response.status_code in [401, 403]

    @patch('app.routes.knowledge.DocumentService.download_document')
    @patch('app.routes.knowledge.os.path.abspath')
    def test_directory_traversal_prevention(
        self, mock_abspath, mock_download_service, authenticated_client, temp_pdf_file
    ):
        """AC3: Prevención de directory traversal"""
        # Setup mocks para simular path malicioso
        mock_abspath.side_effect = [
            "/uploads/safe_path",  # UPLOAD_DIR mock
            "/etc/passwd"          # Path malicioso
        ]
        mock_download_service.return_value = (
            "/etc/passwd", "pdf", "safe.pdf", 1024
        )

        response = authenticated_client.get("/api/knowledge/documents/1/download")

        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "DOCUMENT_NOT_FOUND"


class TestPreviewEndpoint:
    """Tests básicos para endpoint de preview"""

    @patch('app.routes.knowledge.DocumentService.get_document_preview')
    def test_preview_success(self, mock_preview_service, authenticated_client):
        """AC5: Preview exitoso"""
        preview_text = "Este es el contenido del manual para preview. " * 25  # ~500 chars
        mock_preview_service.return_value = preview_text[:500]

        response = authenticated_client.get("/api/knowledge/documents/1/preview")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == 1
        assert data["preview_length"] == 500
        assert len(data["preview"]) == 500

    @patch('app.routes.knowledge.DocumentService.get_document_preview')
    def test_preview_document_not_found(self, mock_preview_service, authenticated_client):
        """AC5: Documento no encontrado retorna 404"""
        mock_preview_service.return_value = None

        response = authenticated_client.get("/api/knowledge/documents/999/preview")

        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "DOCUMENT_NOT_FOUND"

    def test_preview_unauthorized(self):
        """AC2: Preview sin autenticación retorna 401/403"""
        client = TestClient(app)
        response = client.get("/api/knowledge/documents/1/preview")
        assert response.status_code in [401, 403]


class TestDocumentService:
    """Tests unitarios para DocumentService"""

    @pytest.mark.asyncio
    async def test_download_success(self, mock_db_session):
        """Test unitario de download_document exitoso"""
        from app.models.document import Document

        # Mock documento
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            doc = Document(
                id=1,
                title="Test Document",
                file_path=tmp_path,
                file_type="pdf",
                file_size_bytes=12
            )

            mock_query = Mock()
            mock_query.first.return_value = doc
            mock_db_session.exec.return_value = mock_query

            from app.services.document_service import DocumentService
            result = await DocumentService.download_document(1, mock_db_session)

            assert result is not None
            file_path, file_type, safe_filename, file_size = result
            assert file_path == tmp_path
            assert file_type == "pdf"
            assert "Test_Document.pdf" == safe_filename
            assert file_size == 12

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_download_not_found(self, mock_db_session):
        """Test unitario cuando documento no existe"""
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db_session.exec.return_value = mock_query

        from app.services.document_service import DocumentService
        result = await DocumentService.download_document(999, mock_db_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_success(self, mock_db_session):
        """Test unitario de preview exitoso"""
        from app.models.document import Document

        doc = Document(
            id=1,
            title="Test Document",
            content_text="Este es el contenido para preview. " * 100
        )

        mock_query = Mock()
        mock_query.first.return_value = doc
        mock_db_session.exec.return_value = mock_query

        from app.services.document_service import DocumentService
        result = await DocumentService.get_document_preview(1, mock_db_session)

        assert result is not None
        assert len(result) == 500
        assert result == doc.content_text[:500]

    @pytest.mark.asyncio
    async def test_preview_no_content(self, mock_db_session):
        """Test unitario cuando no hay contenido"""
        from app.models.document import Document

        doc = Document(
            id=1,
            title="Test Document",
            content_text=None
        )

        mock_query = Mock()
        mock_query.first.return_value = doc
        mock_db_session.exec.return_value = mock_query

        from app.services.document_service import DocumentService
        result = await DocumentService.get_document_preview(1, mock_db_session)

        assert result is None


class TestSecurityFeatures:
    """Tests específicos para características de seguridad"""

    @patch('app.routes.knowledge.DocumentService.download_document')
    @patch('app.routes.knowledge.os.path.abspath')
    def test_filename_sanitization(self, mock_abspath, mock_download_service,
                                  authenticated_client, temp_pdf_file):
        """Test sanitización de filename en Content-Disposition"""
        mock_abspath.side_effect = lambda x: x
        mock_download_service.return_value = (
            temp_pdf_file, "pdf", "Safe_Document.pdf", 1024
        )

        response = authenticated_client.get("/api/knowledge/documents/1/download")

        # Verificar que filename esté sanitizado (no caracteres especiales)
        content_disposition = response.headers["content-disposition"]
        assert "Safe_Document.pdf" in content_disposition
        assert "<" not in content_disposition  # Sin HTML injection
        assert ">" not in content_disposition
        assert "\"" in content_disposition  # Entrecomillado seguro

    @pytest.mark.asyncio
    async def test_orphaned_file_cleanup(self, mock_db_session):
        """Test cleanup automático de archivos huérfanos"""
        from app.models.document import Document

        doc = Document(
            id=1,
            title="Orphaned Document",
            file_path="/uploads/nonexistent_file.pdf",
            file_type="pdf"
        )

        mock_query = Mock()
        mock_query.first.return_value = doc
        mock_db_session.exec.return_value = mock_query

        from app.services.document_service import DocumentService
        result = await DocumentService.download_document(1, mock_db_session)

        # Verificar que se llamó a delete y commit
        assert result is None
        mock_db_session.delete.assert_called_once_with(doc)
        mock_db_session.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])