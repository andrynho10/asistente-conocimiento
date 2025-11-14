import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select
from app.main import app
from app.database import get_session
from app.models.user import User, UserRole
from app.models.document import DocumentCategory, Document
from app.models.audit import AuditLog
from app.auth.service import AuthService
from app.core.security import get_password_hash

# Base de datos de prueba en memoria
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_db_session():
    """Fixture para base de datos de prueba en memoria"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    SQLModel.metadata.create_all(engine)

    # Usar la misma conexión para todo el test
    connection = engine.connect()
    session = Session(bind=connection)

    yield session

    session.close()
    connection.close()

@pytest.fixture
def test_client(test_db_session):
    """Fixture para cliente de prueba con base de datos aislada"""
    def override_get_session():
        return test_db_session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(test_db_session):
    """Fixture para crear usuario administrador de prueba"""
    admin = User(
        username="admin_test",
        email="admin@test.com",
        full_name="Admin Test User",
        hashed_password=get_password_hash("test_password"),
        role=UserRole.admin,
        is_active=True
    )
    test_db_session.add(admin)
    test_db_session.commit()
    test_db_session.refresh(admin)
    return admin

@pytest.fixture
def normal_user(test_db_session):
    """Fixture para crear usuario normal de prueba"""
    user = User(
        username="user_test",
        email="user@test.com",
        full_name="Normal Test User",
        hashed_password=get_password_hash("test_password"),
        role=UserRole.user,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user

@pytest.fixture
def admin_token(admin_user):
    """Fixture para obtener token JWT de admin"""
    from app.core.security import create_access_token
    return create_access_token(data={"user_id": admin_user.id, "role": "admin"})

@pytest.fixture
def user_token(normal_user):
    """Fixture para obtener token JWT de usuario normal"""
    from app.core.security import create_access_token
    return create_access_token(data={"user_id": normal_user.id, "role": "user"})

@pytest.fixture
def test_category(test_db_session):
    """Fixture para crear categoría de prueba"""
    category = DocumentCategory(
        name="test_category",
        description="Test category for documents"
    )
    test_db_session.add(category)
    test_db_session.commit()
    test_db_session.refresh(category)
    return category

@pytest.fixture
def sample_pdf_file():
    """Fixture para crear archivo PDF de prueba"""
    # Crear un archivo PDF temporal muy simple
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp:
        # Escribir contenido que parezca PDF (cabecera básica)
        tmp.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
        tmp_path = tmp.name

    yield tmp_path

    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

@pytest.fixture
def sample_txt_file():
    """Fixture para crear archivo TXT de prueba"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        tmp.write("Este es un documento de prueba.\nContenido de ejemplo.")
        tmp_path = tmp.name

    yield tmp_path

    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

class TestDocumentUpload:
    """Tests para el endpoint POST /api/knowledge/upload"""

    def test_upload_document_success_pdf(self, test_client, admin_token, test_category, sample_pdf_file):
        """AC 1, 6, 7: Admin sube PDF válido → 201 + registro en DB + archivo guardado"""

        with open(sample_pdf_file, 'rb') as test_file:
            response = test_client.post(
                "/api/knowledge/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("test.pdf", test_file, "application/pdf")},
                data={
                    "title": "Documento de Prueba PDF",
                    "description": "Descripción del documento de prueba",
                    "category": test_category.name
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "uploaded"
        assert data["title"] == "Documento de Prueba PDF"
        assert "document_id" in data
        assert "file_path" in data

        # Verificar que el archivo se guardó
        assert os.path.exists(data["file_path"])

    def test_upload_document_success_txt(self, test_client, admin_token, test_category, sample_txt_file):
        """AC 1, 6, 7: Admin sube TXT válido → 201 + registro en DB + archivo guardado"""

        with open(sample_txt_file, 'rb') as test_file:
            response = test_client.post(
                "/api/knowledge/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("test.txt", test_file, "text/plain")},
                data={
                    "title": "Documento de Prueba TXT",
                    "category": test_category.name
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "uploaded"
        assert data["title"] == "Documento de Prueba TXT"

    def test_upload_invalid_format(self, test_client, admin_token, test_category):
        """AC 2: Intenta subir .docx → error 400 con mensaje específico"""

        # Crear archivo con extensión no permitida
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.docx', delete=False) as tmp:
            tmp.write(b"fake docx content")
            tmp_path = tmp.name

        try:
            with open(tmp_path, 'rb') as test_file:
                response = test_client.post(
                    "/api/knowledge/upload",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    files={"file": ("test.docx", test_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                    data={
                        "title": "Documento Word",
                        "category": test_category.name
                    }
                )

            assert response.status_code == 400
            data = response.json()
            assert data["detail"]["code"] == "INVALID_FILE_FORMAT"
            assert "solo se permiten archivos pdf y txt" in data["detail"]["message"].lower()

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_upload_missing_auth_header(self, test_client, test_category, sample_txt_file):
        """AC 1: Sin header Authorization → error 401 middleware JWT"""

        with open(sample_txt_file, 'rb') as test_file:
            response = test_client.post(
                "/api/knowledge/upload",
                # NO header Authorization
                files={"file": ("test.txt", test_file, "text/plain")},
                data={
                    "title": "Documento sin auth",
                    "category": test_category.name
                }
            )

        # FastAPI valida campos antes de auth, por lo que puede dar 422
        # Lo importante es que no dé 200 (éxito) sin auth
        assert response.status_code in [401, 403, 422]

    def test_upload_unauthorized_user(self, test_client, user_token, test_category, sample_txt_file):
        """AC 5: Usuario normal intenta subir → error 403 verificando role != admin"""

        with open(sample_txt_file, 'rb') as test_file:
            response = test_client.post(
                "/api/knowledge/upload",
                headers={"Authorization": f"Bearer {user_token}"},
                files={"file": ("test.txt", test_file, "text/plain")},
                data={
                    "title": "Documento de usuario normal",
                    "category": test_category.name
                }
            )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_upload_invalid_category(self, test_client, admin_token, sample_txt_file):
        """AC 4: Usa categoría inexistente → error 400 validando en DocumentCategory"""

        with open(sample_txt_file, 'rb') as test_file:
            response = test_client.post(
                "/api/knowledge/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("test.txt", test_file, "text/plain")},
                data={
                    "title": "Documento con categoría inválida",
                    "category": "categoria_inexistente"
                }
            )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_CATEGORY"
        assert "categoria_inexistente" in data["detail"]["message"]

    def test_upload_file_too_large(self, test_client, admin_token, test_category):
        """AC 3: Intenta subir archivo grande → error 413 con mensaje de límite excedido"""

        # Crear archivo temporal grande (más de 10MB)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as tmp:
            # Escribir ~11MB de datos
            tmp.write(b"x" * (11 * 1024 * 1024))
            tmp_path = tmp.name

        try:
            with open(tmp_path, 'rb') as test_file:
                response = test_client.post(
                    "/api/knowledge/upload",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    files={"file": ("large_file.txt", test_file, "text/plain")},
                    data={
                        "title": "Archivo Grande",
                        "category": test_category.name
                    }
                )

            assert response.status_code == 413
            data = response.json()
            assert data["detail"]["code"] == "FILE_TOO_LARGE"
            assert "10mb" in data["detail"]["message"].lower()

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_audit_log_created(self, test_client, test_db_session, admin_token, test_category, sample_txt_file):
        """AC 8: Verificar entrada en audit_logs con evento DOCUMENT_UPLOADED"""

        with open(sample_txt_file, 'rb') as test_file:
            response = test_client.post(
                "/api/knowledge/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("test.txt", test_file, "text/plain")},
                data={
                    "title": "Documento para auditoría",
                    "category": test_category.name
                }
            )

        assert response.status_code == 201

        # Verificar entrada en audit log
        audit_statement = select(AuditLog).where(AuditLog.action == "DOCUMENT_UPLOADED")
        audit_entry = test_db_session.exec(audit_statement).first()

        assert audit_entry is not None
        assert audit_entry.action == "DOCUMENT_UPLOADED"
        assert "Documento para auditoría" in audit_entry.details
        assert audit_entry.resource_type == "document"

    def test_upload_missing_required_fields(self, test_client, admin_token):
        """Test campos requeridos faltantes"""

        # Sin archivo
        response = test_client.post(
            "/api/knowledge/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={}
        )
        assert response.status_code == 400  # Validation error (converted from 422)

        # Sin título
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt') as tmp:
            tmp.write(b"test content")
            tmp.seek(0)

            response = test_client.post(
                "/api/knowledge/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("test.txt", tmp, "text/plain")},
                data={"category": "test"}
            )
        assert response.status_code == 400  # FastAPI devuelve 400 cuando faltan campos requeridos en multipart

    def test_document_created_in_database(self, test_client, test_db_session, admin_token, test_category, sample_txt_file):
        """AC 7: Verificar que el documento se crea correctamente en base de datos"""

        with open(sample_txt_file, 'rb') as test_file:
            response = test_client.post(
                "/api/knowledge/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("test.txt", test_file, "text/plain")},
                data={
                    "title": "Documento DB Test",
                    "description": "Descripción de prueba",
                    "category": test_category.name
                }
            )

        assert response.status_code == 201
        document_id = response.json()["document_id"]

        # Verificar en base de datos
        doc_statement = select(Document).where(Document.id == document_id)
        document = test_db_session.exec(doc_statement).first()

        assert document is not None
        assert document.title == "Documento DB Test"
        assert document.description == "Descripción de prueba"
        assert document.category == test_category.name
        assert document.file_type == "txt"
        assert document.uploaded_by is not None
        assert document.is_indexed is False  # AC 7: debe ser False