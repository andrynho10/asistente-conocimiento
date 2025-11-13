"""
Test debug para identificar problemas con dependency overrides
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.database import get_session
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole


def test_dependency_overrides_debug():
    """Test simple para debug de dependency overrides"""

    # Crear mock de usuario
    def mock_get_current_user():
        return User(
            id=1,
            username="admin",
            email="admin@test.com",
            role=UserRole.admin,
            is_active=True
        )

    # Crear mock de sesión
    def mock_get_session():
        return Mock(spec=Session)

    # Aplicar overrides
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_session] = mock_get_session

    try:
        # Test simple
        with TestClient(app) as client:
            response = client.get("/api/knowledge/documents/1/download")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

    finally:
        # Limpiar overrides
        app.dependency_overrides.clear()


def test_mock_debug():
    """Test para debug de mock de DocumentService"""

    from unittest.mock import AsyncMock

    with patch('app.routes.knowledge.DocumentService.download_document') as mock_download:
        # Mock del servicio
        mock_download.return_value = ("test.pdf", "pdf", "test.pdf", 1024)

        # Mock de usuario y sesión
        def mock_get_current_user():
            return User(
                id=1,
                username="admin",
                email="admin@test.com",
                role=UserRole.admin,
                is_active=True
            )

        def mock_get_session():
            return Mock(spec=Session)

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_session] = mock_get_session

        try:
            with TestClient(app) as client:
                response = client.get("/api/knowledge/documents/1/download")
                print(f"Status Code: {response.status_code}")
                print(f"Mock called: {mock_download.called}")
                print(f"Call count: {mock_download.call_count}")
                if mock_download.called:
                    print(f"Call args: {mock_download.call_args}")

        finally:
            app.dependency_overrides.clear()