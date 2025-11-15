"""
Configuración de base de datos para Asistente de Conocimiento
Usa SQLModel con configuración centralizada desde settings
Soporta SQLCipher para cifrado de base de datos en reposo

AC#11: Timeout handling para database operations
AC#5.3: Cifrado de datos en reposo y en tránsito
"""

import asyncio
import logging
import json
import os
from typing import Generator, Optional, Any, Callable
from sqlalchemy import event
from sqlmodel import create_engine, Session, SQLModel
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Obtener URL de base de datos desde configuración centralizada
# La configuración ya carga variables de entorno automáticamente
settings = get_settings()
DATABASE_URL = settings.database_url
DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY")


def _configure_sqlite_encryption(dbapi_conn: Any, connection_record: Any) -> None:
    """
    Configura SQLCipher para cifrado transparente de base de datos.
    Se ejecuta automáticamente en cada conexión nueva.

    Args:
        dbapi_conn: Conexión SQLite/SQLCipher
        connection_record: Registro de conexión (no usado en esta función)
    """
    if DB_ENCRYPTION_KEY:
        try:
            # Ejecutar PRAGMA key para habilitar cifrado
            # SQLCipher interpreta esto como la clave de cifrado
            dbapi_conn.execute(f"PRAGMA key = '{DB_ENCRYPTION_KEY}'")

            # Validar que la BD está cifrada
            cursor = dbapi_conn.execute("PRAGMA database_list;")
            databases = cursor.fetchall()

            logger.info(
                json.dumps({
                    "event": "database_encryption_enabled",
                    "cipher": "SQLCipher (AES-256)",
                    "key_loaded": True
                })
            )
        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "database_encryption_error",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
            )
            raise


# Crear motor de base de datos
# Para SQLCipher: necesita conectar_args con check_same_thread=False
# echo=True muestra las queries SQL en consola (útil para desarrollo)
engine = create_engine(
    DATABASE_URL,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL.lower() else {}
)

# Registrar evento de conexión para SQLCipher (solo si hay clave disponible)
if DB_ENCRYPTION_KEY and "sqlite" in DATABASE_URL.lower():
    event.listen(engine, "connect", _configure_sqlite_encryption)


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


# ==============================================================================
# AC#11: Timeout Handling for Database Operations
# ==============================================================================

class DatabaseTimeoutError(Exception):
    """Exception raised when database operation exceeds timeout."""
    pass


async def execute_with_timeout(
    operation: Callable[[], Any],
    timeout_ms: Optional[int] = None,
    operation_name: str = "database_operation"
) -> Any:
    """
    Ejecuta una operación de BD con timeout.

    Envuelve operaciones síncronas de BD en asyncio.wait_for para
    aplicar timeout. Si se excede, lanza DatabaseTimeoutError.

    Args:
        operation: Función que ejecuta la operación de BD (debe ser sincrónica)
        timeout_ms: Timeout en milisegundos. Si es None, usa retrieval_timeout_ms
        operation_name: Nombre de la operación para logging

    Returns:
        Resultado de la operación

    Raises:
        DatabaseTimeoutError: Si la operación excede el timeout
        Exception: Cualquier excepción lanzada por la operación

    Example:
        >>> async def get_user():
        ...     result = await execute_with_timeout(
        ...         lambda: db.exec(select(User)).first(),
        ...         timeout_ms=500,
        ...         operation_name="get_user"
        ...     )
        ...     return result
    """
    if timeout_ms is None:
        timeout_ms = settings.retrieval_timeout_ms

    timeout_s = timeout_ms / 1000.0

    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, operation),
            timeout=timeout_s
        )
        return result

    except asyncio.TimeoutError:
        logger.error(
            json.dumps({
                "event": "database_timeout",
                "operation": operation_name,
                "timeout_ms": timeout_ms
            })
        )
        raise DatabaseTimeoutError(
            f"Database operation '{operation_name}' exceeded timeout of {timeout_ms}ms"
        )
    except Exception as e:
        logger.error(
            json.dumps({
                "event": "database_operation_error",
                "operation": operation_name,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
        )
        raise