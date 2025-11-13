"""
Configuración de base de datos para Asistente de Conocimiento
Usa SQLModel con configuración centralizada desde settings
"""

from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from app.core.config import get_settings

# Obtener URL de base de datos desde configuración centralizada
# La configuración ya carga variables de entorno automáticamente
settings = get_settings()
DATABASE_URL = settings.database_url

# Crear motor de base de datos
# echo=True muestra las queries SQL en consola (útil para desarrollo)
engine = create_engine(DATABASE_URL, echo=settings.debug)


def create_db_and_tables() -> None:
    """
    Crea todas las tablas definidas en los modelos SQLModel
    Esta función debe llamarse durante la inicialización de la aplicación

    Nota: Usa 'engine' global para permitir monkey-patching en tests
    """
    import app.database as db_module
    SQLModel.metadata.create_all(db_module.engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI que proporciona una sesión de base de datos

    Returns:
        Generator[Session]: Sesión de base de datos SQLModel

    Usage:
        ```python
        from fastapi import Depends
        from .database import get_session

        @app.get("/users/")
        def read_users(session: Session = Depends(get_session)):
            return session.exec(select(User)).all()
        ```

    Nota: Usa db_module.engine para permitir monkey-patching en tests
    """
    import app.database as db_module
    with Session(db_module.engine) as session:
        yield session