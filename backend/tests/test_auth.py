import pytest
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Las fixtures test_db_session y test_client están definidas en conftest.py
# Este archivo las usa directamente


@pytest.fixture
def client(test_client):
    """Alias para test_client para compatibilidad con tests existentes"""
    return test_client


@pytest.fixture
def test_user(test_db_session):
    """Crea un usuario de prueba en la BD de testing"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        role=UserRole.user,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(test_db_session):
    """Crea un usuario administrador de prueba"""
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpassword"),
        role=UserRole.admin,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
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
        assert response.status_code == 401  # No authorization header (Unauthorized)

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