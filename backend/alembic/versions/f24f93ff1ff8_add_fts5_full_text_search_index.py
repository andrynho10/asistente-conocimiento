"""add fts5 full text search index

Revision ID: f24f93ff1ff8
Revises: 3336ed844a79
Create Date: 2025-11-13 09:02:11.473875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f24f93ff1ff8'
down_revision: Union[str, Sequence[str], None] = '3336ed844a79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crea tabla virtual FTS5 para búsqueda full-text de documentos.

    Configuración:
    - Tokenizer: unicode61 remove_diacritics 2 (soporte español completo)
    - Normalización: Búsqueda insensible a acentos y mayúsculas
    - Ranking: BM25 integrado en FTS5
    - Triggers: Sincronización automática con tabla documents
    """
    # Crear tabla virtual FTS5 para búsqueda full-text
    # content='documents' vincula con tabla source
    # content_rowid='id' mapea el rowid de documents
    # tokenize configura el procesamiento de texto en español
    op.execute("""
        CREATE VIRTUAL TABLE documents_fts USING fts5(
            document_id UNINDEXED,
            title,
            content_text,
            category,
            content='documents',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        )
    """)

    # Trigger INSERT: Agregar documento nuevo al índice FTS5 (solo si tiene content_text)
    op.execute("""
        CREATE TRIGGER documents_ai AFTER INSERT ON documents
        WHEN new.content_text IS NOT NULL
        BEGIN
            INSERT INTO documents_fts(document_id, title, content_text, category)
            VALUES (new.id, new.title, new.content_text, new.category);
        END
    """)

    # Trigger UPDATE: Actualizar documento en índice FTS5
    op.execute("""
        CREATE TRIGGER documents_au AFTER UPDATE ON documents BEGIN
            UPDATE documents_fts
            SET title = new.title,
                content_text = new.content_text,
                category = new.category
            WHERE document_id = old.id;
        END
    """)

    # Trigger DELETE: Eliminar documento del índice FTS5
    op.execute("""
        CREATE TRIGGER documents_ad AFTER DELETE ON documents BEGIN
            DELETE FROM documents_fts WHERE document_id = old.id;
        END
    """)

    # Backfill: Insertar documentos existentes en tabla FTS5
    # Solo inserta documentos que tienen content_text (ya extraído)
    op.execute("""
        INSERT INTO documents_fts(document_id, title, content_text, category)
        SELECT id, title, content_text, category
        FROM documents
        WHERE content_text IS NOT NULL
    """)


def downgrade() -> None:
    """Elimina tabla FTS5 y triggers asociados."""
    # Eliminar triggers primero
    op.execute("DROP TRIGGER IF EXISTS documents_ad")
    op.execute("DROP TRIGGER IF EXISTS documents_au")
    op.execute("DROP TRIGGER IF EXISTS documents_ai")

    # Eliminar tabla virtual FTS5
    op.execute("DROP TABLE IF EXISTS documents_fts")
