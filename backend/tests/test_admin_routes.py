"""
Tests for Admin Routes

Test cases for admin dashboard endpoints:
- GET /api/admin/generated-content (list with filters)
- PUT /api/admin/generated-content/{id}/validate
- DELETE /api/admin/generated-content/{id}
- GET /api/admin/quiz/{id}/stats
- GET /api/admin/learning-path/{id}/stats
- GET /api/admin/generated-content/export
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import (
    User,
    Document,
    GeneratedContent,
    UserRole,
    ContentType,
    AuditLog,
)
from app.core.security import create_access_token


@pytest.fixture(name="session")
def session_fixture():
    """Create in-memory SQLite database for tests"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create all tables
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with mocked session"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="admin_user")
def admin_user_fixture(session: Session):
    """Create admin user for tests"""
    user = User(
        username="admin_test",
        email="admin@test.com",
        full_name="Admin Test",
        hashed_password="hashed",
        role=UserRole.admin,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="regular_user")
def regular_user_fixture(session: Session):
    """Create regular user for tests"""
    user = User(
        username="user_test",
        email="user@test.com",
        full_name="User Test",
        hashed_password="hashed",
        role=UserRole.user,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_document")
def test_document_fixture(session: Session, admin_user: User):
    """Create test document"""
    doc = Document(
        filename="test_doc.pdf",
        file_path="/uploads/test_doc.pdf",
        uploaded_by=admin_user.id,
        file_size=1024,
        mime_type="application/pdf"
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


@pytest.fixture(name="test_content")
def test_content_fixture(
    session: Session, regular_user: User, test_document: Document
):
    """Create test generated content"""
    content = GeneratedContent(
        document_id=test_document.id,
        user_id=regular_user.id,
        content_type=ContentType.SUMMARY,
        content_json={"summary": "Test summary content"},
        is_validated=False
    )
    session.add(content)
    session.commit()
    session.refresh(content)
    return content


class TestAdminListContent:
    """Tests for GET /api/admin/generated-content"""

    def test_list_content_as_admin(
        self, client: TestClient, admin_user: User, test_content: GeneratedContent
    ):
        """AC1: Admin can list generated content"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/admin/generated-content", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["items"]) > 0

    def test_list_content_as_regular_user_forbidden(
        self, client: TestClient, regular_user: User
    ):
        """AC1: Regular users cannot access admin endpoints"""
        token = create_access_token(regular_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/admin/generated-content", headers=headers)
        assert response.status_code == 403

    def test_list_content_without_auth(self, client: TestClient):
        """AC1: Unauthenticated users get 401"""
        response = client.get("/api/admin/generated-content")
        assert response.status_code == 401

    def test_filter_by_type(
        self, client: TestClient, admin_user: User, test_content: GeneratedContent
    ):
        """AC4: Filter by content type works"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/admin/generated-content?type=summary",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["content_type"] == "summary" for item in data["items"])

    def test_filter_by_invalid_type_returns_400(
        self, client: TestClient, admin_user: User
    ):
        """Filter by invalid type returns 400"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/admin/generated-content?type=invalid",
            headers=headers
        )
        assert response.status_code == 400

    def test_pagination(self, client: TestClient, admin_user: User, session: Session):
        """AC9: Pagination works correctly"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        # Create multiple items
        for i in range(5):
            content = GeneratedContent(
                document_id=1,
                user_id=admin_user.id,
                content_type=ContentType.QUIZ,
                content_json={"quiz": f"Test {i}"}
            )
            session.add(content)
        session.commit()

        response = client.get(
            "/api/admin/generated-content?limit=2&offset=0",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert len(data["items"]) <= 2


class TestAdminValidateContent:
    """Tests for PUT /api/admin/generated-content/{id}/validate"""

    def test_validate_content(
        self, client: TestClient, admin_user: User, test_content: GeneratedContent
    ):
        """AC16: Admin can mark content as validated"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.put(
            f"/api/admin/generated-content/{test_content.id}/validate",
            json={"is_validated": True},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_validated"] is True

    def test_validate_nonexistent_content(
        self, client: TestClient, admin_user: User
    ):
        """Validating nonexistent content returns 404"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.put(
            "/api/admin/generated-content/99999/validate",
            json={"is_validated": True},
            headers=headers
        )
        assert response.status_code == 404


class TestAdminDeleteContent:
    """Tests for DELETE /api/admin/generated-content/{id}"""

    def test_delete_content_soft_delete(
        self, client: TestClient, admin_user: User, test_content: GeneratedContent, session: Session
    ):
        """AC13: Delete performs soft delete (marks deleted_at)"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.delete(
            f"/api/admin/generated-content/{test_content.id}",
            headers=headers
        )
        assert response.status_code == 204

        # Verify soft delete
        from sqlmodel import select
        stmt = select(GeneratedContent).where(GeneratedContent.id == test_content.id)
        deleted_content = session.exec(stmt).first()
        assert deleted_content is not None
        assert deleted_content.deleted_at is not None

    def test_delete_nonexistent_content_returns_404(
        self, client: TestClient, admin_user: User
    ):
        """Deleting nonexistent content returns 404"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.delete(
            "/api/admin/generated-content/99999",
            headers=headers
        )
        assert response.status_code == 404


class TestAdminExport:
    """Tests for GET /api/admin/generated-content/export"""

    def test_export_csv(
        self, client: TestClient, admin_user: User, test_content: GeneratedContent
    ):
        """AC17: Export as CSV works"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/admin/generated-content/export?format=csv",
            headers=headers
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"

    def test_export_invalid_format_returns_400(
        self, client: TestClient, admin_user: User
    ):
        """Invalid export format returns 400"""
        token = create_access_token(admin_user)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/admin/generated-content/export?format=invalid",
            headers=headers
        )
        assert response.status_code == 400
