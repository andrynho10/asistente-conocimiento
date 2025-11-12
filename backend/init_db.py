#!/usr/bin/env python3
"""
Script de inicialización de base de datos para Asistente de Conocimiento

Crea todas las tablas, inserta usuario administrador inicial y categorías predefinidas
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del app al path para poder importar modelos
sys.path.append(str(Path(__file__).parent))

from sqlmodel import Session, select
import bcrypt
from app.database import engine
from app.models import User, UserRole, Document

# Categorías predefinidas
PREDEFINED_CATEGORIES = [
    "Políticas RRHH",
    "Procedimientos Operativos",
    "Manuales Técnicos"
]


def create_admin_user(session: Session) -> None:
    """Crea usuario administrador inicial si no existe"""
    admin_username = "admin"

    # Verificar si admin ya existe
    stmt = select(User).where(User.username == admin_username)
    existing_admin = session.exec(stmt).first()

    if existing_admin:
        print("INFO  Usuario administrador ya existe")
        return

    # Crear usuario admin con hash manual
    password = "admin123"
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

    admin_user = User(
        username=admin_username,
        email="admin@example.com",
        full_name="Administrador del Sistema",
        hashed_password=hashed_password,
        role=UserRole.admin,
        is_active=True
    )

    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)

    print(f"OK Usuario administrador creado: {admin_user.username}")
    print(f"   Email: {admin_user.email}")
    print(f"   Contraseña: admin123 (¡cambiar en producción!)")


def create_predefined_categories(session: Session) -> None:
    """Inserta categorías predefinidas como documentos de ejemplo"""
    admin_user = session.exec(select(User).where(User.username == "admin")).first()

    if not admin_user:
        print("ERROR No se puede crear categorías: no existe usuario admin")
        return

    categories_created = 0
    for category_name in PREDEFINED_CATEGORIES:
        # Verificar si ya existe un documento para esta categoría
        stmt = select(Document).where(
            Document.title == f"Categoría: {category_name}",
            Document.uploaded_by == admin_user.id
        )
        existing = session.exec(stmt).first()

        if existing:
            print(f"INFO  Categoría ya existe: {category_name}")
            continue

        # Crear documento de categoría
        category_doc = Document(
            title=f"Categoría: {category_name}",
            category=category_name,
            file_path=f"/categories/{category_name.lower().replace(' ', '_')}.md",
            file_type="txt",
            file_size_bytes=0,
            uploaded_by=admin_user.id
        )

        session.add(category_doc)
        categories_created += 1

    session.commit()

    if categories_created > 0:
        print(f"OK Se crearon {categories_created} categorías predefinidas:")
        for cat in PREDEFINED_CATEGORIES:
            print(f"   - {cat}")
    else:
        print("INFO  Todas las categorías predefinidas ya existen")


def create_sample_documents(session: Session) -> None:
    """Crea algunos documentos de ejemplo para testing"""
    admin_user = session.exec(select(User).where(User.username == "admin")).first()

    if not admin_user:
        return

    sample_docs = [
        {
            "title": "Manual deEmpleado",
            "category": "Políticas RRHH",
            "file_path": "/docs/manual_empleado.pdf",
            "file_type": "pdf",
            "file_size_bytes": 1024000  # 1MB
        },
        {
            "title": "Procedimiento deOnboarding",
            "category": "Procedimientos Operativos",
            "file_path": "/docs/procedimiento_onboarding.pdf",
            "file_type": "pdf",
            "file_size_bytes": 512000  # 512KB
        }
    ]

    docs_created = 0
    for doc_data in sample_docs:
        # Verificar si ya existe
        stmt = select(Document).where(
            Document.file_path == doc_data["file_path"]
        )
        existing = session.exec(stmt).first()

        if existing:
            continue

        doc = Document(
            uploaded_by=admin_user.id,
            **doc_data
        )
        session.add(doc)
        docs_created += 1

    session.commit()

    if docs_created > 0:
        print(f"OK Se crearon {docs_created} documentos de ejemplo")


def init_database():
    """Función principal de inicialización de base de datos"""
    print("Inicializando base de datos del Asistente de Conocimiento...")

    try:
        # Crear tablas
        from app.database import create_db_and_tables
        create_db_and_tables()
        print("OK Tablas creadas exitosamente")

        # Usar sesión para insertar datos iniciales
        with Session(engine) as session:
            # Crear usuario administrador
            create_admin_user(session)

            # Crear categorías predefinidas
            create_predefined_categories(session)

            # Crear documentos de ejemplo
            create_sample_documents(session)

        print("\nSUCCESS Base de datos inicializada correctamente!")
        print("LOCATION Ubicación: database/asistente_conocimiento.db")
        print("\nKEY Acceso inicial:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("\nWARNING  Importante: Cambiar la contraseña del administrador en producción")

    except Exception as e:
        print(f"ERROR Error al inicializar la base de datos: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()