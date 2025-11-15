"""
Tests for User Password Management Routes

Test cases for user password endpoints:
- POST /api/users/change-password (change password)
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import User, UserRole, AuditLog
from app.core.security import create_access_token, get_password_hash, verify_password


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


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("OldPass123!"),
        role=UserRole.user,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_token")
def test_token_fixture(test_user: User):
    """Generate JWT token for test user"""
    return create_access_token(data={
        "sub": str(test_user.id),
        "user_id": test_user.id,
        "role": test_user.role.value
    })


class TestChangePassword:
    """Tests for POST /api/users/change-password"""

    def test_change_password_success(self, client: TestClient, test_token: str, test_user: User, session: Session):
        """Test changing password with valid data"""
        response = client.post(
            "/api/users/change-password",
            headers={"Authorization": f"Bearer {test_token}"},
            params={
                "current_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"]

        # Verify password was changed
        session.refresh(test_user)
        assert verify_password("NewPass456!", test_user.hashed_password)
        assert not verify_password("OldPass123!", test_user.hashed_password)

    def test_change_password_wrong_current_password(self, client: TestClient, test_token: str):
        """Test changing password with wrong current password fails"""
        response = client.post(
            "/api/users/change-password",
            headers={"Authorization": f"Bearer {test_token}"},
            params={
                "current_password": "WrongPass123!",
                "new_password": "NewPass456!"
            }
        )
        assert response.status_code == 400
        assert "INVALID_PASSWORD" in response.json()["detail"]["code"]

    def test_change_password_weak_new_password(self, client: TestClient, test_token: str):
        """Test changing password to weak password fails"""
        response = client.post(
            "/api/users/change-password",
            headers={"Authorization": f"Bearer {test_token}"},
            params={
                "current_password": "OldPass123!",
                "new_password": "weak"
            }
        )
        assert response.status_code == 400
        assert "WEAK_PASSWORD" in response.json()["detail"]["code"]

    def test_change_password_new_equals_username(self, client: TestClient, test_token: str):
        """Test changing password to username fails"""
        response = client.post(
            "/api/users/change-password",
            headers={"Authorization": f"Bearer {test_token}"},
            params={
                "current_password": "OldPass123!",
                "new_password": "testuser"  # Exact match with username (lowercase)
            }
        )
        # Note: This password is weak anyway (no uppercase, special char, etc) and also equals username
        assert response.status_code == 400

    def test_change_password_requires_auth(self, client: TestClient):
        """Test that unauthenticated user cannot change password"""
        response = client.post(
            "/api/users/change-password",
            params={
                "current_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        )
        assert response.status_code == 401

    def test_change_password_creates_audit_log(self, client: TestClient, test_token: str, test_user: User, session: Session):
        """Test that audit log is created on successful password change"""
        response = client.post(
            "/api/users/change-password",
            headers={"Authorization": f"Bearer {test_token}"},
            params={
                "current_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        )
        assert response.status_code == 200

        # Check audit log
        from sqlmodel import select
        audit_logs = session.exec(
            select(AuditLog).where(AuditLog.action == "PASSWORD_CHANGED")
        ).all()
        assert len(audit_logs) > 0
        assert audit_logs[-1].user_id == test_user.id
        assert audit_logs[-1].resource_type == "user"

    def test_change_password_creates_failed_audit_log(self, client: TestClient, test_token: str, test_user: User, session: Session):
        """Test that audit log is created on failed password change attempt"""
        response = client.post(
            "/api/users/change-password",
            headers={"Authorization": f"Bearer {test_token}"},
            params={
                "current_password": "WrongPass123!",
                "new_password": "NewPass456!"
            }
        )
        assert response.status_code == 400

        # Check audit log for failed attempt
        from sqlmodel import select
        audit_logs = session.exec(
            select(AuditLog).where(AuditLog.action == "PASSWORD_CHANGE_FAILED")
        ).all()
        assert len(audit_logs) > 0
        assert audit_logs[-1].user_id == test_user.id

    def test_change_password_various_special_chars(self, client: TestClient, test_token: str, test_user: User, session: Session):
        """Test changing password with various special characters"""
        special_passwords = [
            "NewPass@123!",
            "NewPass#456$",
            "NewPass%789^",
            "NewPass&123*"
        ]

        for idx, new_password in enumerate(special_passwords):
            # Use different test token for each iteration (create new user)
            user = User(
                username=f"user{idx}",
                email=f"user{idx}@example.com",
                full_name=f"User {idx}",
                hashed_password=get_password_hash("OldPass123!"),
                role=UserRole.user
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            token = create_access_token(data={
                "sub": str(user.id),
                "user_id": user.id,
                "role": user.role.value
            })

            response = client.post(
                "/api/users/change-password",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "current_password": "OldPass123!",
                    "new_password": new_password
                }
            )
            assert response.status_code == 200, f"Failed for password: {new_password}"

    def test_change_password_updates_timestamp(self, client: TestClient, test_token: str, test_user: User, session: Session):
        """Test that user updated_at timestamp is updated"""
        old_timestamp = test_user.updated_at

        response = client.post(
            "/api/users/change-password",
            headers={"Authorization": f"Bearer {test_token}"},
            params={
                "current_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        )
        assert response.status_code == 200

        # Verify timestamp was updated
        session.refresh(test_user)
        assert test_user.updated_at > old_timestamp
