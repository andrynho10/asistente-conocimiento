"""
Tests for User Management Admin Routes

Test cases for admin user management endpoints:
- POST /api/admin/users (create user)
- GET /api/admin/users (list users)
- PUT /api/admin/users/{user_id} (update user)
- PATCH /api/admin/users/{user_id}/deactivate (deactivate user)
- PATCH /api/admin/users/{user_id}/unlock (unlock user)
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import User, UserRole, AuditLog
from app.core.security import create_access_token, get_password_hash


@pytest.fixture(name="session")
def session_fixture():
    """Create in-memory SQLite database for tests"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
    """Create an admin user for testing"""
    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("AdminPass123!"),
        role=UserRole.admin,
        is_active=True
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


@pytest.fixture(name="admin_token")
def admin_token_fixture(admin_user: User):
    """Generate admin JWT token for testing"""
    return create_access_token(data={
        "sub": str(admin_user.id),
        "user_id": admin_user.id,
        "role": admin_user.role.value
    })


@pytest.fixture(name="regular_user")
def regular_user_fixture(session: Session):
    """Create a regular user for testing"""
    user = User(
        username="regularuser",
        email="regular@example.com",
        full_name="Regular User",
        hashed_password=get_password_hash("RegularPass123!"),
        role=UserRole.user,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="regular_token")
def regular_token_fixture(regular_user: User):
    """Generate regular JWT token for testing"""
    return create_access_token(data={
        "sub": str(regular_user.id),
        "user_id": regular_user.id,
        "role": regular_user.role.value
    })


class TestCreateUser:
    """Tests for POST /api/admin/users"""

    def test_create_user_success(self, client: TestClient, admin_token: str):
        """Test creating a user with valid data"""
        response = client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "username": "newuser",
                "password": "NewPass123!",
                "full_name": "New User",
                "email": "newuser@example.com",
                "role": "user"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert "hashed_password" not in data
        assert "password" not in data

    def test_create_user_weak_password(self, client: TestClient, admin_token: str):
        """Test creating user with weak password fails"""
        response = client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "username": "newuser",
                "password": "weak",
                "full_name": "New User",
                "email": "newuser@example.com"
            }
        )
        assert response.status_code == 400
        assert "WEAK_PASSWORD" in response.json()["detail"]["code"]

    def test_create_user_duplicate_username(self, client: TestClient, admin_token: str, admin_user: User):
        """Test creating user with duplicate username fails"""
        response = client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "username": admin_user.username,
                "password": "NewPass123!",
                "full_name": "New User",
                "email": "different@example.com"
            }
        )
        assert response.status_code == 409
        assert "USERNAME_EXISTS" in response.json()["detail"]["code"]

    def test_create_user_duplicate_email(self, client: TestClient, admin_token: str, admin_user: User):
        """Test creating user with duplicate email fails"""
        response = client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "username": "newuser",
                "password": "NewPass123!",
                "full_name": "New User",
                "email": admin_user.email
            }
        )
        assert response.status_code == 409
        assert "EMAIL_EXISTS" in response.json()["detail"]["code"]

    def test_create_user_invalid_role(self, client: TestClient, admin_token: str):
        """Test creating user with invalid role fails"""
        response = client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "username": "newuser",
                "password": "NewPass123!",
                "full_name": "New User",
                "email": "newuser@example.com",
                "role": "superuser"
            }
        )
        assert response.status_code == 400
        assert "INVALID_ROLE" in response.json()["detail"]["code"]

    def test_create_user_requires_admin(self, client: TestClient, regular_token: str):
        """Test that non-admin cannot create user"""
        response = client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {regular_token}"},
            params={
                "username": "newuser",
                "password": "NewPass123!",
                "full_name": "New User",
                "email": "newuser@example.com"
            }
        )
        assert response.status_code == 403


class TestListUsers:
    """Tests for GET /api/admin/users"""

    def test_list_users_success(self, client: TestClient, admin_token: str, session: Session):
        """Test listing users with pagination"""
        # Create a few test users
        for i in range(3):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                hashed_password=get_password_hash("Pass123!"),
                role=UserRole.user
            )
            session.add(user)
        session.commit()

        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 20, "offset": 0}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "users" in data
        assert data["limit"] == 20
        assert data["offset"] == 0
        # Should have at least 4 users (admin + 3 test users)
        assert len(data["users"]) >= 4

    def test_list_users_hides_passwords(self, client: TestClient, admin_token: str):
        """Test that passwords are not returned in list"""
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert "hashed_password" not in user
            assert "password" not in user

    def test_list_users_requires_admin(self, client: TestClient, regular_token: str):
        """Test that non-admin cannot list users"""
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403


class TestUpdateUser:
    """Tests for PUT /api/admin/users/{user_id}"""

    def test_update_user_success(self, client: TestClient, admin_token: str, regular_user: User):
        """Test updating user with valid data"""
        response = client.put(
            f"/api/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "full_name": "Updated Name",
                "email": "updated@example.com",
                "role": "admin"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"
        assert data["role"] == "admin"
        # Username should not change
        assert data["username"] == "regularuser"

    def test_update_user_duplicate_email(self, client: TestClient, admin_token: str, admin_user: User, regular_user: User):
        """Test updating user with duplicate email fails"""
        response = client.put(
            f"/api/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"email": admin_user.email}
        )
        assert response.status_code == 409
        assert "EMAIL_EXISTS" in response.json()["detail"]["code"]

    def test_update_user_not_found(self, client: TestClient, admin_token: str):
        """Test updating non-existent user fails"""
        response = client.put(
            "/api/admin/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"full_name": "Updated"}
        )
        assert response.status_code == 404

    def test_update_user_invalid_role(self, client: TestClient, admin_token: str, regular_user: User):
        """Test updating user with invalid role fails"""
        response = client.put(
            f"/api/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"role": "superuser"}
        )
        assert response.status_code == 400
        assert "INVALID_ROLE" in response.json()["detail"]["code"]

    def test_update_user_requires_admin(self, client: TestClient, regular_token: str, admin_user: User):
        """Test that non-admin cannot update user"""
        response = client.put(
            f"/api/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {regular_token}"},
            params={"full_name": "Updated"}
        )
        assert response.status_code == 403


class TestDeactivateUser:
    """Tests for PATCH /api/admin/users/{user_id}/deactivate"""

    def test_deactivate_user_success(self, client: TestClient, admin_token: str, regular_user: User, session: Session):
        """Test deactivating a user"""
        response = client.patch(
            f"/api/admin/users/{regular_user.id}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "User deactivated successfully" in data["message"]

        # Verify user is deactivated in database
        session.refresh(regular_user)
        assert regular_user.is_active is False

    def test_deactivate_user_not_found(self, client: TestClient, admin_token: str):
        """Test deactivating non-existent user fails"""
        response = client.patch(
            "/api/admin/users/99999/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_deactivate_user_requires_admin(self, client: TestClient, regular_token: str, admin_user: User):
        """Test that non-admin cannot deactivate user"""
        response = client.patch(
            f"/api/admin/users/{admin_user.id}/deactivate",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403


class TestUnlockUser:
    """Tests for PATCH /api/admin/users/{user_id}/unlock"""

    def test_unlock_user_success(self, client: TestClient, admin_token: str, regular_user: User, session: Session):
        """Test unlocking a user"""
        # Set user as locked
        regular_user.failed_login_attempts = 5
        session.add(regular_user)
        session.commit()

        response = client.patch(
            f"/api/admin/users/{regular_user.id}/unlock",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "unlocked successfully" in data["message"]

        # Verify user is unlocked
        session.refresh(regular_user)
        assert regular_user.failed_login_attempts == 0
        assert regular_user.locked_until is None

    def test_unlock_user_not_found(self, client: TestClient, admin_token: str):
        """Test unlocking non-existent user fails"""
        response = client.patch(
            "/api/admin/users/99999/unlock",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_unlock_user_requires_admin(self, client: TestClient, regular_token: str, admin_user: User):
        """Test that non-admin cannot unlock user"""
        response = client.patch(
            f"/api/admin/users/{admin_user.id}/unlock",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403


class TestAuditLogging:
    """Tests for audit log creation on user operations"""

    def test_audit_log_on_user_created(self, client: TestClient, admin_token: str, session: Session, admin_user: User):
        """Test that audit log is created when user is created"""
        response = client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "username": "audituser",
                "password": "AuditPass123!",
                "full_name": "Audit User",
                "email": "audit@example.com"
            }
        )
        assert response.status_code == 201

        # Check audit log
        from sqlmodel import select
        audit_logs = session.exec(
            select(AuditLog).where(AuditLog.action == "USER_CREATED")
        ).all()
        assert len(audit_logs) > 0
        assert audit_logs[-1].user_id == admin_user.id
        assert audit_logs[-1].resource_type == "user"

    def test_audit_log_on_user_updated(self, client: TestClient, admin_token: str, regular_user: User, session: Session, admin_user: User):
        """Test that audit log is created when user is updated"""
        response = client.put(
            f"/api/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"full_name": "Updated"}
        )
        assert response.status_code == 200

        # Check audit log
        from sqlmodel import select
        audit_logs = session.exec(
            select(AuditLog).where(AuditLog.action == "USER_UPDATED")
        ).all()
        assert len(audit_logs) > 0
        assert audit_logs[-1].user_id == admin_user.id
        assert audit_logs[-1].resource_id == regular_user.id

    def test_audit_log_on_user_deactivated(self, client: TestClient, admin_token: str, regular_user: User, session: Session, admin_user: User):
        """Test that audit log is created when user is deactivated"""
        response = client.patch(
            f"/api/admin/users/{regular_user.id}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

        # Check audit log
        from sqlmodel import select
        audit_logs = session.exec(
            select(AuditLog).where(AuditLog.action == "USER_DEACTIVATED")
        ).all()
        assert len(audit_logs) > 0
        assert audit_logs[-1].user_id == admin_user.id
        assert audit_logs[-1].resource_id == regular_user.id
