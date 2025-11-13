"""
Configuración de pytest para tests del backend.

Este archivo define fixtures compartidas y configuración global para pytest.
Maneja la configuración de base de datos de prueba antes de importar los modelos.
"""
import pytest
import os
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

# CRÍTICO: Establecer entorno de testing ANTES de importar la app
os.environ["FASTAPI_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-must-be-at-least-32-characters-long-for-jwt-signing"
os.environ["OLLAMA_HOST"] = "http://localhost:11434"
os.environ["DEBUG"] = "true"

from sqlmodel import Session, create_engine, SQLModel
from fastapi.testclient import TestClient

# CRÍTICO: Importar TODOS los modelos ANTES de create_engine
# para que SQLModel.metadata registre las tablas
from app.models.user import User, UserRole
from app.models.document import Document, DocumentCategory
from app.models.audit import AuditLog
from app.core.security import get_password_hash

from app.main import app
from app.database import get_session
from app import database  # Importar módulo completo para monkey-patching


@pytest.fixture
def project_root():
    """Retorna la ruta raíz del proyecto."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def backend_root():
    """Retorna la ruta raíz del backend."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="function")
def test_engine():
    """
    Fixture que crea un engine de base de datos en memoria para cada test.

    El mismo engine se reutiliza en test_db_session y test_client
    para garantizar consistencia en toda la prueba.

    CRÍTICO: Reemplaza el engine global en database.py para que FastAPI
    use el mismo engine que el resto de los tests.
    """
    from sqlalchemy.pool import StaticPool

    # Crear engine de prueba con StaticPool para evitar threads
    test_db_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # CRITICAL: Monkey-patch PRIMERO el engine global en database.py
    # Esto asegura que get_session() use el mismo engine que nuestros tests
    old_engine = database.engine
    database.engine = test_db_engine

    # DESPUÉS de parchear, crear las tablas
    SQLModel.metadata.create_all(test_db_engine)

    yield test_db_engine

    # Cleanup: drop all tables y restaurar engine original
    SQLModel.metadata.drop_all(test_db_engine)
    database.engine = old_engine


@pytest.fixture
def test_db_session(test_engine):
    """
    Fixture para base de datos de prueba en memoria.

    Usa el mismo engine que test_client para consistencia.
    """
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def test_db(test_engine):
    """Alias de test_db_session para compatibilidad"""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def test_client(test_engine, test_db_session):
    """
    Fixture para cliente de prueba con base de datos aislada.

    Usa la misma sesión que test_db_session para garantizar que los datos
    creados en fixtures (como test_user) estén disponibles en el cliente HTTP.
    CRÍTICO: Recibe test_engine explícitamente para asegurar que las tablas
    se crean antes de que el cliente inicie.

    IMPORTANTE: El TestClient ejecuta el lifespan de FastAPI que llama a
    create_db_and_tables() usando database.engine. Por eso monkey-patcheamos
    el engine ANTES de crear el cliente.
    """
    # Override la dependencia ANTES de crear el TestClient
    def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session

    # El TestClient ahora usará database.engine (ya parchado) para create_db_and_tables()
    client = TestClient(app)

    yield client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True, scope="function")
def setup_test_client_globals(test_client, request):
    """
    Fixture que inyecta el test_client en módulos de tests que lo usan como variable global.
    Permite que tests escritos sin fixture como parámetro sigan funcionando.
    """
    # Solo aplicar a módulos específicos que tenemos que arreglar
    if "test_document_listing" in request.node.fspath.strpath or \
       "test_document_download" in request.node.fspath.strpath or \
       "test_download_integration" in request.node.fspath.strpath:
        # Inyectar test_client en el módulo de tests
        import sys
        module = sys.modules[request.node.module.__name__]
        old_client = getattr(module, 'client', None)
        module.client = test_client

        yield

        # Restaurar estado original
        if old_client is not None:
            module.client = old_client
        elif hasattr(module, 'client'):
            delattr(module, 'client')
    else:
        yield


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


@pytest.fixture
def isolated_env_for_config_tests():
    """
    Fixture que aísla variables de entorno para tests de configuración.
    Restaura os.environ después del test para no afectar otros tests.
    """
    # Guardar estado actual de variables de entorno críticas
    original_env = {}
    critical_vars = ["DATABASE_URL", "SECRET_KEY", "OLLAMA_HOST", "FASTAPI_ENV", "DEBUG"]

    for var in critical_vars:
        original_env[var] = os.environ.get(var)

    # Limpiar estas variables para tests de config
    for var in critical_vars:
        if var in os.environ:
            del os.environ[var]

    yield

    # Restaurar estado original
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]
