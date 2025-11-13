"""
Tests para DocumentService y endpoints de listado de documentos (Story 2.5).

Tests unitarios para service layer y tests de integración para endpoints.
Cubre todos los acceptance criteria y casos límite.
"""

import pytest
from datetime import datetime, timezone
from sqlmodel import Session, select
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_session, create_db_and_tables
from app.models.user import User, UserRole
from app.models.document import Document, DocumentCategory, DocumentResponse, DocumentListRequest, CategoryResponse
from app.services.document_service import DocumentService
from app.core.security import create_access_token

client = None  # Será inyectado por setup_test_client_globals en conftest.py


@pytest.fixture
def db_session(test_db_session):
    """Fixture para crear sesión de base de datos para tests"""
    yield test_db_session
    # Limpiar datos después del test
    try:
        test_db_session.exec("DELETE FROM documents")
        test_db_session.exec("DELETE FROM document_categories")
        test_db_session.exec("DELETE FROM user")
        test_db_session.commit()
    except:
        test_db_session.rollback()


@pytest.fixture
def admin_user(db_session: Session):
    """Fixture para crear usuario admin"""
    user = User(
        username="admin",
        email="admin@test.com",
        full_name="Admin User",
        hashed_password="hashed_password",
        role=UserRole.admin,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session: Session):
    """Fixture para crear usuario regular"""
    user = User(
        username="user",
        email="user@test.com",
        full_name="Regular User",
        hashed_password="hashed_password",
        role=UserRole.user,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_admin(admin_user: User):
    """Fixture para headers de autenticación admin"""
    token = create_access_token(data={"user_id": admin_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user(regular_user: User):
    """Fixture para headers de autenticación usuario regular"""
    token = create_access_token(data={"user_id": regular_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_categories(db_session: Session):
    """Fixture para crear categorías de prueba"""
    categories = [
        DocumentCategory(name="manual", description="Manuales de usuario"),
        DocumentCategory(name="policy", description="Políticas internas"),
        DocumentCategory(name="technical", description="Documentación técnica")
    ]
    for cat in categories:
        db_session.add(cat)
    db_session.commit()
    return categories


@pytest.fixture
def sample_documents(db_session: Session, admin_user: User, sample_categories):
    """Fixture para crear documentos de prueba"""
    documents = [
        Document(
            title="Manual de Usuario",
            description="Guía completa del sistema",
            category="manual",
            file_type="pdf",
            file_size_bytes=1024000,
            file_path="/uploads/manual_usuario.pdf",
            uploaded_by=admin_user.id,
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="Política de Vacaciones",
            description="Normas de vacaciones y permisos",
            category="policy",
            file_type="pdf",
            file_size_bytes=512000,
            file_path="/uploads/politica_vacaciones.pdf",
            uploaded_by=admin_user.id,
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="API Documentation",
            description="Documentación de endpoints REST",
            category="technical",
            file_type="txt",
            file_size_bytes=256000,
            file_path="/uploads/api_docs.txt",
            uploaded_by=admin_user.id,
            is_indexed=False
        )
    ]
    for doc in documents:
        db_session.add(doc)
    db_session.commit()
    return documents


class TestDocumentService:
    """Tests unitarios para DocumentService"""

    @pytest.mark.asyncio
    async def test_get_documents_default_pagination(self, db_session: Session, sample_documents):
        """AC1: Test listado sin filtros con paginación por defecto (limit=20, offset=0)"""
        documents = await DocumentService.get_documents(db_session)

        assert len(documents) == 3
        assert all(isinstance(doc, DocumentResponse) for doc in documents)
        # Verificar ordenamiento por defecto (upload_date desc)
        assert documents[0].upload_date >= documents[1].upload_date
        assert documents[1].upload_date >= documents[2].upload_date

    @pytest.mark.asyncio
    async def test_get_documents_with_pagination(self, db_session: Session, sample_documents):
        """AC2: Test paginación con diferentes limit/offset"""
        # Test limit=1
        documents = await DocumentService.get_documents(db_session, limit=1)
        assert len(documents) == 1

        # Test offset=1
        documents = await DocumentService.get_documents(db_session, limit=2, offset=1)
        assert len(documents) == 2

    @pytest.mark.asyncio
    async def test_get_documents_filter_by_category(self, db_session: Session, sample_documents):
        """AC2: Test filtrado por categoría válida"""
        documents = await DocumentService.get_documents(db_session, category="manual")
        assert len(documents) == 1
        assert documents[0].category == "manual"
        assert documents[0].title == "Manual de Usuario"

    @pytest.mark.asyncio
    async def test_get_documents_filter_nonexistent_category(self, db_session: Session, sample_documents):
        """AC2: Test filtrado por categoría inexistente retorna lista vacía"""
        documents = await DocumentService.get_documents(db_session, category="nonexistent")
        assert len(documents) == 0

    @pytest.mark.asyncio
    async def test_get_documents_sort_by_upload_date(self, db_session: Session, sample_documents):
        """AC5: Test ordenamiento por upload_date asc/desc"""
        # Desc (default)
        documents_desc = await DocumentService.get_documents(db_session, sort_by="upload_date", order="desc")
        assert documents_desc[0].upload_date >= documents_desc[1].upload_date

        # Asc
        documents_asc = await DocumentService.get_documents(db_session, sort_by="upload_date", order="asc")
        assert documents_asc[0].upload_date <= documents_asc[1].upload_date

    @pytest.mark.asyncio
    async def test_get_documents_sort_by_title(self, db_session: Session, sample_documents):
        """AC5: Test ordenamiento por title asc/desc"""
        # Asc
        documents_asc = await DocumentService.get_documents(db_session, sort_by="title", order="asc")
        titles_asc = [doc.title for doc in documents_asc]
        assert titles_asc == sorted(titles_asc)

        # Desc
        documents_desc = await DocumentService.get_documents(db_session, sort_by="title", order="desc")
        titles_desc = [doc.title for doc in documents_desc]
        assert titles_desc == sorted(titles_desc, reverse=True)

    @pytest.mark.asyncio
    async def test_get_documents_sort_by_file_size(self, db_session: Session, sample_documents):
        """AC5: Test ordenamiento por file_size_bytes asc/desc"""
        # Asc
        documents_asc = await DocumentService.get_documents(db_session, sort_by="file_size_bytes", order="asc")
        sizes_asc = [doc.file_size_bytes for doc in documents_asc]
        assert sizes_asc == sorted(sizes_asc)

        # Desc
        documents_desc = await DocumentService.get_documents(db_session, sort_by="file_size_bytes", order="desc")
        sizes_desc = [doc.file_size_bytes for doc in documents_desc]
        assert sizes_desc == sorted(sizes_desc, reverse=True)

    @pytest.mark.asyncio
    async def test_get_documents_invalid_sort_field(self, db_session: Session):
        """AC5: Test ordenamiento con campo inválido retorna error"""
        with pytest.raises(ValueError, match="Campo de ordenamiento no permitido"):
            await DocumentService.get_documents(db_session, sort_by="invalid_field")

    @pytest.mark.asyncio
    async def test_get_documents_invalid_order(self, db_session: Session):
        """AC5: Test ordenamiento con dirección inválida retorna error"""
        with pytest.raises(ValueError, match="Dirección de ordenamiento no permitida"):
            await DocumentService.get_documents(db_session, order="invalid")

    @pytest.mark.asyncio
    async def test_get_document_by_id_exists(self, db_session: Session, sample_documents):
        """AC3: Test detalle de documento existente retorna 200"""
        doc_id = sample_documents[0].id
        document = await DocumentService.get_document_by_id(doc_id, db_session)

        assert document is not None
        assert isinstance(document, DocumentResponse)
        assert document.id == doc_id
        assert document.title == sample_documents[0].title

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_exists(self, db_session: Session):
        """AC3: Test detalle de documento inexistente retorna 404"""
        document = await DocumentService.get_document_by_id(999, db_session)
        assert document is None

    @pytest.mark.asyncio
    async def test_get_categories_with_documents(self, db_session: Session, sample_documents):
        """AC4: Test listado de categorías con contador correcto"""
        categories = await DocumentService.get_categories(db_session)

        assert len(categories) == 3
        assert all(isinstance(cat, CategoryResponse) for cat in categories)

        # Verificar contadores
        category_counts = {cat.name: cat.document_count for cat in categories}
        assert category_counts["manual"] == 1
        assert category_counts["policy"] == 1
        assert category_counts["technical"] == 1

    @pytest.mark.asyncio
    async def test_get_categories_empty_documents(self, db_session: Session, sample_categories):
        """AC4: Test categorías sin documentos retornan contador=0"""
        categories = await DocumentService.get_categories(db_session)

        assert len(categories) == 3
        assert all(cat.document_count == 0 for cat in categories)

    @pytest.mark.asyncio
    async def test_get_uploaded_by_username(self, db_session: Session, admin_user: User, sample_documents):
        """Test que uploaded_by se convierte a username"""
        documents = await DocumentService.get_documents(db_session)

        assert all(doc.uploaded_by == admin_user.username for doc in documents)
        # Verificar que no es el ID numérico
        assert all(doc.uploaded_by != str(admin_user.id) for doc in documents)


class TestDocumentEndpoints:
    """Tests de integración para endpoints"""

    def test_list_documents_success_admin(self, auth_headers_admin, sample_documents):
        """AC1: Test listado de documentos con admin"""
        response = client.get("/api/knowledge/documents", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_list_documents_success_user(self, auth_headers_user, sample_documents):
        """AC6: Test usuario 'user' puede listar documentos (readonly)"""
        response = client.get("/api/knowledge/documents", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_list_documents_unauthorized(self, sample_documents):
        """Test usuario sin token retorna 401"""
        response = client.get("/api/knowledge/documents")

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_list_documents_with_filters(self, auth_headers_admin, sample_documents):
        """AC2: Test listado con filtros"""
        response = client.get(
            "/api/knowledge/documents?category=manual&limit=5&offset=0&sort_by=title&order=asc",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "manual"

    def test_list_documents_invalid_sort_field(self, auth_headers_admin):
        """AC5: Test ordenamiento con campo inválido retorna 400"""
        response = client.get(
            "/api/knowledge/documents?sort_by=invalid_field",
            headers=auth_headers_admin
        )

        assert response.status_code == 400
        assert "INVALID_PARAMETERS" in response.json()["code"]

    def test_get_document_success(self, auth_headers_admin, sample_documents):
        """AC3: Test obtener documento existente"""
        doc_id = sample_documents[0].id
        response = client.get(f"/api/knowledge/documents/{doc_id}", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert data["title"] == sample_documents[0].title

    def test_get_document_not_found(self, auth_headers_admin):
        """AC3: Test obtener documento inexistente retorna 404"""
        response = client.get("/api/knowledge/documents/999", headers=auth_headers_admin)

        assert response.status_code == 404
        assert "DOCUMENT_NOT_FOUND" in response.json()["code"]

    def test_get_categories_success(self, auth_headers_admin, sample_documents):
        """AC4: Test listado de categorías"""
        response = client.get("/api/knowledge/categories", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert all("name" in cat and "document_count" in cat for cat in data)

    def test_get_categories_unauthorized(self):
        """Test categorías sin token retorna 401"""
        response = client.get("/api/knowledge/categories")

        assert response.status_code == 401


class TestPerformanceRequirements:
    """Tests para verificar requisitos de performance"""

    @pytest.mark.asyncio
    async def test_list_documents_performance(self, db_session: Session, sample_documents):
        """Test que response time < 300ms para listado básico (RNF2)"""
        import time

        start_time = time.time()
        documents = await DocumentService.get_documents(db_session)
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 300  # Performance requirement
        assert len(documents) == 3

    @pytest.mark.asyncio
    async def test_get_document_performance(self, db_session: Session, sample_documents):
        """Test performance para obtener documento individual"""
        import time

        doc_id = sample_documents[0].id

        start_time = time.time()
        document = await DocumentService.get_document_by_id(doc_id, db_session)
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 100  # Should be faster than list
        assert document is not None

    @pytest.mark.asyncio
    async def test_get_categories_performance(self, db_session: Session, sample_documents):
        """Test performance para listar categorías"""
        import time

        start_time = time.time()
        categories = await DocumentService.get_categories(db_session)
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 200  # Should be fast with aggregation
        assert len(categories) == 3


class TestEdgeCases:
    """Tests para casos límite y validación"""

    @pytest.mark.asyncio
    async def test_empty_database(self, db_session: Session):
        """Test comportamiento con base de datos vacía"""
        documents = await DocumentService.get_documents(db_session)
        assert documents == []

        categories = await DocumentService.get_categories(db_session)
        assert categories == []

        document = await DocumentService.get_document_by_id(1, db_session)
        assert document is None

    @pytest.mark.asyncio
    async def test_extreme_pagination_values(self, db_session: Session, sample_documents):
        """Test con valores extremos de paginación"""
        # Limit mayor al número de documentos
        documents = await DocumentService.get_documents(db_session, limit=100)
        assert len(documents) == 3

        # Offset mayor al número de documentos
        documents = await DocumentService.get_documents(db_session, offset=100)
        assert len(documents) == 0

    @pytest.mark.asyncio
    async def test_unicode_characters(self, db_session: Session, admin_user: User):
        """Test con caracteres unicode en títulos y descripciones"""
        doc = Document(
            title="Título con ñ y áéíóú",
            description="Descripción con caracteres especiales: €@#$%&",
            category="manual",
            file_type="txt",
            file_size_bytes=1000,
            file_path="/uploads/unicode_test.txt",
            uploaded_by=admin_user.id
        )
        db_session.add(doc)
        db_session.commit()

        documents = await DocumentService.get_documents(db_session)
        assert len(documents) == 1
        assert "ñ" in documents[0].title
        assert "€" in documents[0].description