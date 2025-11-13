"""
Configuración de pytest para tests del backend.

Este archivo define fixtures compartidas y configuración global para pytest.
"""
import pytest
import os
import tempfile
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_session
from app.models.user import User, UserRole
from app.models.document import DocumentCategory
from app.core.security import get_password_hash


@pytest.fixture
def project_root():
    """Retorna la ruta raíz del proyecto."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def backend_root():
    """Retorna la ruta raíz del backend."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="function")
def test_db():
    """
    Fixture con base de datos en memoria para tests.

    Crea una base de datos SQLite en memoria para cada test,
    garantizando aislamiento entre tests.
    """
    # Crear motor en memoria
    test_engine = create_engine("sqlite:///:memory:", echo=False)

    # Crear todas las tablas definidas en SQLModel
    SQLModel.metadata.create_all(test_engine)

    # Proporcionar sesión para el test
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def test_db_session():
    """Fixture para base de datos de prueba en memoria (alias de test_db para compatibilidad)"""
    engine = create_engine(
        "sqlite:///:memory:",
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
