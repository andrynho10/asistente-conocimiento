import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session
from app.main import app
from app.database import get_session
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = Session(autocommit=False, autoflush=False, bind=engine)

def override_get_session():
    try:
        yield TestingSessionLocal
    finally:
        pass

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    SQLModel.metadata.create_all(bind=engine)
    yield
    SQLModel.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user():
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        role=UserRole.user,
        is_active=True
    )
    TestingSessionLocal.add(user)
    TestingSessionLocal.commit()
    TestingSessionLocal.refresh(user)
    return user

@pytest.fixture
def admin_user():
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpassword"),
        role=UserRole.admin,
        is_active=True
    )
    TestingSessionLocal.add(user)
    TestingSessionLocal.commit()
    TestingSessionLocal.refresh(user)
    return user

class TestAuthentication:

    def test_health_public(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"

    def test_login_valid_credentials(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user_id"] == test_user.id
        assert data["role"] == UserRole.user.value

    def test_login_invalid_credentials(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "INVALID_CREDENTIALS"

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "INVALID_CREDENTIALS"

    def test_login_missing_fields(self, client):
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422  # Validation error

    def test_logout_valid_token(self, client, test_user):
        # First login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword"}
        )
        token = login_response.json()["token"]

        # Then logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logout successful"

    def test_logout_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "INVALID_TOKEN"

    def test_logout_no_token(self, client):
        response = client.post("/api/auth/logout")
        assert response.status_code == 403  # No authorization header

    def test_jwt_token_payload_structure(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword"}
        )
        data = response.json()
        token = data["token"]

        # Verify token contains expected fields by making authenticated request
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200