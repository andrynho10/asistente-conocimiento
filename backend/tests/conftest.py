"""
Configuración de pytest para tests del backend.

Este archivo define fixtures compartidas y configuración global para pytest.
"""
import pytest
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel


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
