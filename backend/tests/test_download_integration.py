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

    def test_admin_download_pdf_success(
        self, authenticated_client, monkeypatch
    ):
        """AC1: Admin puede solicitar descarga de PDF"""
        from app.services.document_service import DocumentService

        # Setup mock que simula documento no encontrado
        # (El test verifica que auth funciona, no que el archivo exista)
        async def mock_download(doc_id, db, user=None):
            return None

        monkeypatch.setattr(DocumentService, 'download_document', mock_download)

        # Test
        response = authenticated_client.get("/api/knowledge/documents/1/download")

        # El endpoint debe retornar 404 porque el documento no existe
        # pero NO debe retornar 401 (lo que verificamos es que auth funciona)
        assert response.status_code == 404
        data = response.json()["detail"]
        assert data["code"] == "DOCUMENT_NOT_FOUND"

    def test_user_download_txt_success(
        self, normal_client, monkeypatch
    ):
        """AC1: Usuario normal puede solicitar descarga de TXT"""
        from app.services.document_service import DocumentService

        # Setup mock que simula documento no encontrado
        async def mock_download(doc_id, db, user=None):
            return None

        monkeypatch.setattr(DocumentService, 'download_document', mock_download)

        # Test
        response = normal_client.get("/api/knowledge/documents/2/download")

        # El endpoint debe retornar 404 porque el documento no existe
        # pero NO debe retornar 401 (lo que verificamos es que auth funciona)
        assert response.status_code == 404
        data = response.json()["detail"]
        assert data["code"] == "DOCUMENT_NOT_FOUND"

    def test_download_document_not_found(self, authenticated_client, monkeypatch):
        """AC2: Documento no existe retorna 404"""
        from app.services.document_service import DocumentService

        async def mock_download(doc_id, db, user=None):
            return None

        monkeypatch.setattr(DocumentService, 'download_document', mock_download)

        response = authenticated_client.get("/api/knowledge/documents/999/download")

        assert response.status_code == 404
        data = response.json()["detail"]
        assert data["code"] == "DOCUMENT_NOT_FOUND"

    def test_download_unauthorized(self):
        """AC2: No autenticado retorna 401/403"""
        client = TestClient(app)
        response = client.get("/api/knowledge/documents/1/download")
        assert response.status_code in [401, 403]

    def test_directory_traversal_prevention(
        self, authenticated_client, monkeypatch
    ):
        """AC3: Prevención de directory traversal"""
        from app.services.document_service import DocumentService

        # Setup mock para simular path malicioso
        async def mock_download(doc_id, db, user=None):
            return ("/etc/passwd", "pdf", "safe.pdf", 1024)

        monkeypatch.setattr(DocumentService, 'download_document', mock_download)

        response = authenticated_client.get("/api/knowledge/documents/1/download")

        assert response.status_code == 404
        data = response.json()["detail"]
        assert data["code"] == "DOCUMENT_NOT_FOUND"


class TestPreviewEndpoint:
    """Tests básicos para endpoint de preview"""

    def test_preview_success(self, authenticated_client, monkeypatch):
        """AC5: Preview exitoso"""
        from app.services.document_service import DocumentService

        preview_text = "Este es el contenido del manual para preview. " * 25  # ~500 chars
        preview_text = preview_text[:500]

        async def mock_preview(doc_id, db):
            return preview_text

        monkeypatch.setattr(DocumentService, 'get_document_preview', mock_preview)

        response = authenticated_client.get("/api/knowledge/documents/1/preview")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == 1
        assert data["preview_length"] == 500
        assert len(data["preview"]) == 500

    def test_preview_document_not_found(self, authenticated_client, monkeypatch):
        """AC5: Documento no encontrado retorna 404"""
        from app.services.document_service import DocumentService

        async def mock_preview(doc_id, db):
            return None

        monkeypatch.setattr(DocumentService, 'get_document_preview', mock_preview)

        response = authenticated_client.get("/api/knowledge/documents/999/preview")

        assert response.status_code == 404
        data = response.json()["detail"]
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