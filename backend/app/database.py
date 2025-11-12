"""
Configuración de base de datos para Asistente de Conocimiento
Usa SQLModel con SQLite para desarrollo local
"""

import os
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener URL de base de datos desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/asistente_conocimiento.db")

# Crear motor de base de datos
# echo=True muestra las queries SQL en consola (útil para desarrollo)
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    """
    Crea todas las tablas definidas en los modelos SQLModel
    Esta función debe llamarse durante la inicialización de la aplicación
    """
    SQLModel.metadata.create_all(engine)


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
    """
    with Session(engine) as session:
        yield session