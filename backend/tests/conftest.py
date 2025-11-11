"""
Configuración de pytest para tests del backend.

Este archivo define fixtures compartidas y configuración global para pytest.
"""
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Retorna la ruta raíz del proyecto."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def backend_root():
    """Retorna la ruta raíz del backend."""
    return Path(__file__).parent.parent
