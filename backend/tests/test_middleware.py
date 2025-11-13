import pytest
from fastapi.testclient import TestClient
from fastapi import APIRouter, Depends
from app.main import app
from app.middleware.auth import get_current_user, require_role
from app.models.user import User, UserRole

# Create a test endpoint to test middleware
test_router = APIRouter()

@test_router.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    return {"message": "Protected endpoint", "user_id": current_user.id}

@test_router.get("/admin-only")
async def admin_endpoint(current_user: User = Depends(get_current_user), _=Depends(require_role("admin"))):
    return {"message": "Admin only endpoint", "user_id": current_user.id}

app.include_router(test_router, prefix="/test", tags=["test"])

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user_with_token(client):
    # Create user and login
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "role": "user"
    }

    # Note: In a real test, you'd need to create the user in the database
    # For now, we'll just test the middleware behavior with invalid tokens

    return user_data

class TestMiddleware:

    def test_protected_endpoint_without_token(self, client):
        response = client.get("/test/protected")
        assert response.status_code == 401  # No authorization header (Unauthorized)

    def test_protected_endpoint_with_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/test/protected", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "INVALID_TOKEN"

    def test_admin_endpoint_without_token(self, client):
        response = client.get("/test/admin-only")
        assert response.status_code == 401  # No authorization header (Unauthorized)

    def test_admin_endpoint_with_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/test/admin-only", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "INVALID_TOKEN"