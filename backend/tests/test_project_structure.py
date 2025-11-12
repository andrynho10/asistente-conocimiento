"""
Tests de validación de la estructura del proyecto.

Verifica que todos los archivos y carpetas clave existan según los acceptance criteria.
"""
import os
from pathlib import Path
import pytest
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def test_backend_directory_structure_exists(project_root):
    """AC #1: Verifica que existe la estructura de carpetas del backend."""
    backend_dirs = [
        "backend/app",
        "backend/app/models",
        "backend/app/routes",
        "backend/app/services",
        "backend/app/utils",
        "backend/app/schemas",
        "backend/app/api",
        "backend/app/core",
        "backend/tests",
        "backend/alembic",
    ]

    for dir_path in backend_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directorio {dir_path} no existe"
        assert full_path.is_dir(), f"{dir_path} no es un directorio"


def test_frontend_directory_structure_exists(project_root):
    """AC #1: Verifica que existe la estructura de carpetas del frontend."""
    frontend_dirs = [
        "frontend/src",
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/store",
        "frontend/src/services",
        "frontend/src/types",
        "frontend/src/hooks",
        "frontend/src/lib",
        "frontend/src/styles",
    ]

    for dir_path in frontend_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directorio {dir_path} no existe"
        assert full_path.is_dir(), f"{dir_path} no es un directorio"


def test_root_directories_exist(project_root):
    """AC #1: Verifica que existen carpetas raíz del proyecto."""
    root_dirs = ["backend", "frontend", "database", "docs"]

    for dir_name in root_dirs:
        full_path = project_root / dir_name
        assert full_path.exists(), f"Directorio {dir_name} no existe"
        assert full_path.is_dir(), f"{dir_name} no es un directorio"


def test_pyproject_toml_exists(backend_root):
    """AC #2: Verifica que existe el archivo pyproject.toml."""
    pyproject_path = backend_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml no existe"
    assert pyproject_path.is_file(), "pyproject.toml no es un archivo"


def test_pyproject_toml_has_required_dependencies(backend_root):
    """AC #2: Verifica que pyproject.toml contiene todas las dependencias requeridas."""
    pyproject_path = backend_root / "pyproject.toml"

    with open(pyproject_path, 'rb') as f:
        config = tomllib.load(f)

    dependencies = config['tool']['poetry']['dependencies']

    # Dependencias core requeridas según AC #2
    required_deps = {
        'fastapi': '0.115.0',
        'sqlmodel': '0.0.14',
        'python-jose': '3.3.0',
        'passlib': '1.7.4',
        'python-multipart': '0.0.9',
        'python-dotenv': True,  # Solo verificar que existe
    }

    for dep, version in required_deps.items():
        assert dep in dependencies, f"Dependencia {dep} no está en pyproject.toml"
        if version is not True:
            # Verificar versión exacta o compatible
            dep_version = dependencies[dep]
            if isinstance(dep_version, dict):
                dep_version = dep_version.get('version', '')
            assert version in dep_version or dep_version.startswith('^'), \
                f"Dependencia {dep} tiene versión incorrecta: {dep_version} (esperado: {version})"


def test_pyproject_toml_has_pytest(backend_root):
    """AC #2: Verifica que pytest está configurado como dependencia de desarrollo."""
    pyproject_path = backend_root / "pyproject.toml"

    with open(pyproject_path, 'rb') as f:
        config = tomllib.load(f)

    dev_dependencies = config['tool']['poetry']['group']['dev']['dependencies']
    assert 'pytest' in dev_dependencies, "pytest no está en dependencias de desarrollo"


def test_env_example_exists(backend_root):
    """AC #3: Verifica que existe el archivo .env.example."""
    env_example_path = backend_root / ".env.example"
    assert env_example_path.exists(), ".env.example no existe en backend/"
    assert env_example_path.is_file(), ".env.example no es un archivo"


def test_env_example_has_required_variables(backend_root):
    """AC #3: Verifica que .env.example contiene todas las variables requeridas."""
    env_example_path = backend_root / ".env.example"

    with open(env_example_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'JWT_EXPIRATION_HOURS',
        'OLLAMA_HOST',
        'OLLAMA_MODEL',
    ]

    for var in required_vars:
        assert var in content, f"Variable de entorno {var} no está en .env.example"

    # Verificar valores específicos mencionados en AC #3
    assert 'sqlite:///./asistente_conocimiento.db' in content, "DATABASE_URL por defecto no está correcto"
    assert 'http://localhost:11434' in content, "OLLAMA_HOST por defecto no está correcto"
    assert 'llama3.1:8b-instruct-q4_K_M' in content, "OLLAMA_MODEL por defecto no está correcto"


def test_readme_exists(project_root):
    """AC #4: Verifica que existe el archivo README.md."""
    readme_path = project_root / "README.md"
    assert readme_path.exists(), "README.md no existe"
    assert readme_path.is_file(), "README.md no es un archivo"


def test_readme_has_required_sections(project_root):
    """AC #4: Verifica que README.md contiene secciones requeridas."""
    readme_path = project_root / "README.md"

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()

    required_sections = [
        'instalación',
        'ejecución',
        'requisitos',
    ]

    for section in required_sections:
        assert section in content, f"Sección '{section}' no está en README.md"


def test_gitignore_exists(project_root):
    """AC #5: Verifica que existe el archivo .gitignore."""
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), ".gitignore no existe"
    assert gitignore_path.is_file(), ".gitignore no es un archivo"


def test_gitignore_has_python_exclusions(project_root):
    """AC #5: Verifica que .gitignore contiene exclusiones para Python."""
    gitignore_path = project_root / ".gitignore"

    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar que existen patrones equivalentes o más completos
    assert '__pycache__' in content, "Exclusión '__pycache__' no está en .gitignore"
    assert ('*.pyc' in content or '*.py[cod]' in content), "Exclusión para archivos .pyc no está en .gitignore"
    assert 'venv/' in content, "Exclusión 'venv/' no está en .gitignore"
    assert '.env' in content, "Exclusión '.env' no está en .gitignore"
    assert '*.db' in content, "Exclusión '*.db' no está en .gitignore"


def test_gitignore_has_nodejs_exclusions(project_root):
    """AC #5: Verifica que .gitignore contiene exclusiones para Node.js."""
    gitignore_path = project_root / ".gitignore"

    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()

    nodejs_exclusions = [
        'node_modules/',
        'dist/',
    ]

    for exclusion in nodejs_exclusions:
        assert exclusion in content, f"Exclusión '{exclusion}' no está en .gitignore"


def test_git_repository_initialized(project_root):
    """AC #5: Verifica que el repositorio Git fue inicializado."""
    git_dir = project_root / ".git"
    assert git_dir.exists(), "Repositorio Git no fue inicializado (.git no existe)"
    assert git_dir.is_dir(), ".git no es un directorio"


def test_frontend_package_json_exists(project_root):
    """Verifica que existe el archivo package.json del frontend."""
    package_json_path = project_root / "frontend" / "package.json"
    assert package_json_path.exists(), "package.json no existe en frontend/"
    assert package_json_path.is_file(), "package.json no es un archivo"


def test_frontend_env_example_exists(project_root):
    """Verifica que existe .env.example en frontend."""
    env_example_path = project_root / "frontend" / ".env.example"
    assert env_example_path.exists(), ".env.example no existe en frontend/"

    with open(env_example_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'VITE_API_URL' in content, "VITE_API_URL no está en frontend/.env.example"


def test_conftest_exists(backend_root):
    """Verifica que existe conftest.py para pytest."""
    conftest_path = backend_root / "tests" / "conftest.py"
    assert conftest_path.exists(), "conftest.py no existe en backend/tests/"
    assert conftest_path.is_file(), "conftest.py no es un archivo"
