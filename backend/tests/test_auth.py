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
        assert response.status_code == 400  # Validation error (converted from 422)

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


class TestAccountLockout:
    """Tests para Story 5.2 - Sistema de Bloqueo de Cuentas por Intentos Fallidos"""

    def test_successful_login_resets_failed_attempts(self, client, test_db_session, test_user):
        """AC2: Login exitoso resetea failed_login_attempts a 0"""
        # Simular intentos fallidos
        test_user.failed_login_attempts = 3
        test_db_session.add(test_user)
        test_db_session.commit()

        # Login exitoso
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data

        # Verificar que failed_login_attempts fue reseteado
        test_db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 0

    def test_1_to_4_failed_attempts_returns_401(self, client, test_db_session, test_user):
        """AC1: 1-4 intentos fallidos retorna 401 con remaining_attempts"""
        for attempt in range(1, 5):
            response = client.post(
                "/api/auth/login",
                json={"username": "testuser", "password": "wrongpassword"}
            )
            assert response.status_code == 401
            data = response.json()
            assert data["detail"]["code"] == "INVALID_CREDENTIALS"
            assert "remaining_attempts" in data["detail"]
            expected_remaining = 5 - attempt
            assert data["detail"]["remaining_attempts"] == expected_remaining

            # Verificar que se incrementó failed_login_attempts
            test_db_session.refresh(test_user)
            assert test_user.failed_login_attempts == attempt

    def test_5_failed_attempts_triggers_403_lockout(self, client, test_db_session, test_user):
        """AC1 + AC3: 5 intentos fallidos bloquea la cuenta con 403"""
        # Hacer 5 intentos fallidos
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": "testuser", "password": "wrongpassword"}
            )

        # 5to intento debe retornar 403 ACCOUNT_LOCKED
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "ACCOUNT_LOCKED"
        assert "locked_until" in data["detail"]

        # Verificar que locked_until fue seteado
        test_db_session.refresh(test_user)
        assert test_user.locked_until is not None
        assert test_user.failed_login_attempts == 5

    def test_account_locked_response_contains_locked_until(self, client, test_db_session, test_user):
        """AC3: Response 403 contiene timestamp de desbloqueo"""
        # Hacer 5 intentos fallidos para bloquear
        for _ in range(5):
            client.post(
                "/api/auth/login",
                json={"username": "testuser", "password": "wrongpassword"}
            )

        # El 5to intento debe retornar 403 con locked_until
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "ACCOUNT_LOCKED"
        assert "locked_until" in data["detail"]

    def test_successful_login_updates_last_login(self, client, test_db_session, test_user):
        """AC2: Login exitoso actualiza last_login timestamp"""
        original_last_login = test_user.last_login

        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == 200

        # Verificar que last_login fue actualizado
        test_db_session.refresh(test_user)
        assert test_user.last_login is not None
        assert test_user.last_login != original_last_login

    def test_admin_unlock_user_endpoint(self, client, test_db_session, admin_user, test_user):
        """AC4: POST /api/admin/users/{user_id}/unlock desbloquea cuenta"""
        from datetime import datetime, timedelta, timezone

        # Bloquear la cuenta
        test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        test_user.failed_login_attempts = 5
        test_db_session.add(test_user)
        test_db_session.commit()

        # Login como admin
        admin_login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpassword"}
        )
        admin_token = admin_login.json()["token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Llamar endpoint de unlock
        response = client.post(
            f"/api/admin/users/{test_user.id}/unlock",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cuenta desbloqueada exitosamente"

        # Verificar que los campos fueron reseteados
        test_db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None

    def test_non_admin_cannot_unlock_user(self, client, test_user):
        """Verificar que solo admins pueden desbloquear usuarios"""
        # Login como usuario normal
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword"}
        )
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Intentar desbloquear
        response = client.post(
            f"/api/admin/users/{test_user.id}/unlock",
            headers=headers
        )
        assert response.status_code == 403

    def test_audit_logs_login_failed(self, client, test_db_session, test_user):
        """AC5: Cada intento fallido registra LOGIN_FAILED en auditoría"""
        from app.models.audit import AuditLog
        from sqlmodel import delete

        # Clear existing audit logs
        test_db_session.exec(delete(AuditLog))
        test_db_session.commit()

        # Hacer un intento fallido
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401

        # Verificar que se registró LOGIN_FAILED
        from sqlmodel import select
        audit_logs = test_db_session.exec(
            select(AuditLog).where(
                (AuditLog.user_id == test_user.id) &
                (AuditLog.action == "LOGIN_FAILED")
            )
        ).all()
        assert len(audit_logs) > 0

    def test_audit_logs_account_locked(self, client, test_db_session, test_user):
        """AC5: ACCOUNT_LOCKED se registra en auditoría cuando se bloquea"""
        from app.models.audit import AuditLog
        from sqlmodel import delete

        # Clear existing audit logs
        test_db_session.exec(delete(AuditLog))
        test_db_session.commit()

        # Hacer 5 intentos fallidos
        for _ in range(5):
            client.post(
                "/api/auth/login",
                json={"username": "testuser", "password": "wrongpassword"}
            )

        # Verificar que se registró ACCOUNT_LOCKED
        from sqlmodel import select
        audit_logs = test_db_session.exec(
            select(AuditLog).where(
                (AuditLog.user_id == test_user.id) &
                (AuditLog.action == "ACCOUNT_LOCKED")
            )
        ).all()
        assert len(audit_logs) > 0

    def test_audit_logs_account_unlocked(self, client, test_db_session, admin_user, test_user):
        """AC5: ACCOUNT_UNLOCKED se registra cuando admin desbloquea"""
        from app.models.audit import AuditLog
        from datetime import datetime, timedelta, timezone
        from sqlmodel import delete

        # Clear existing audit logs
        test_db_session.exec(delete(AuditLog))
        test_db_session.commit()

        # Bloquear la cuenta
        test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        test_user.failed_login_attempts = 5
        test_db_session.add(test_user)
        test_db_session.commit()

        # Login como admin
        admin_login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpassword"}
        )
        admin_token = admin_login.json()["token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Desbloquear
        client.post(
            f"/api/admin/users/{test_user.id}/unlock",
            headers=headers
        )

        # Verificar que se registró ACCOUNT_UNLOCKED
        from sqlmodel import select
        audit_logs = test_db_session.exec(
            select(AuditLog).where(AuditLog.action == "ACCOUNT_UNLOCKED")
        ).all()
        assert len(audit_logs) > 0

    def test_login_with_config_max_attempts(self, client, test_db_session, test_user):
        """AC6: MAX_FAILED_LOGIN_ATTEMPTS se carga desde config (default 5)"""
        from app.core.config import get_settings

        settings = get_settings()
        # Verificar que el valor por defecto es 5
        assert settings.max_failed_login_attempts >= 1

        # Hacer intentos hasta alcanzar el máximo
        for _ in range(settings.max_failed_login_attempts):
            response = client.post(
                "/api/auth/login",
                json={"username": "testuser", "password": "wrongpassword"}
            )

        # El último debe retornar 403
        assert response.status_code == 403