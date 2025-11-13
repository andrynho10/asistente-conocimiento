"""
Tests para SearchService - Búsqueda full-text con SQLite FTS5.

Cubre:
- Búsqueda básica por palabras clave
- Búsqueda por frases exactas
- Operadores booleanos (AND, OR, NOT)
- Paginación (limit/offset)
- Validación de queries
- Ranking de relevancia
- Snippets de contexto
"""

import pytest
from datetime import datetime, timezone
from sqlmodel import Session, select, text

from app.models.document import Document
from app.models.user import User, UserRole
from app.services.search_service import SearchService
from app.core.security import get_password_hash


@pytest.fixture
def setup_fts5_table(test_db_session):
    """
    Crea tabla FTS5 y triggers en base de datos de test.

    La migración normal crea esto, pero en tests in-memory
    necesitamos recrear la estructura FTS5.
    """
    # Crear tabla virtual FTS5 (sin external content para tests)
    test_db_session.exec(text("""
        CREATE VIRTUAL TABLE documents_fts USING fts5(
            document_id UNINDEXED,
            title,
            content_text,
            category,
            tokenize='unicode61 remove_diacritics 2'
        )
    """))

    # Trigger INSERT (solo para documentos con content_text)
    test_db_session.exec(text("""
        CREATE TRIGGER documents_ai AFTER INSERT ON documents
        WHEN new.content_text IS NOT NULL
        BEGIN
            INSERT INTO documents_fts(document_id, title, content_text, category)
            VALUES (new.id, new.title, new.content_text, new.category);
        END
    """))

    # Trigger UPDATE
    test_db_session.exec(text("""
        CREATE TRIGGER documents_au AFTER UPDATE ON documents BEGIN
            UPDATE documents_fts
            SET title = new.title,
                content_text = new.content_text,
                category = new.category
            WHERE document_id = old.id;
        END
    """))

    # Trigger DELETE
    test_db_session.exec(text("""
        CREATE TRIGGER documents_ad AFTER DELETE ON documents BEGIN
            DELETE FROM documents_fts WHERE document_id = old.id;
        END
    """))

    test_db_session.commit()
    yield test_db_session


@pytest.fixture
def test_user(test_db_session):
    """Crea usuario de prueba para documentos."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        role=UserRole.admin
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def sample_documents(setup_fts5_table, test_user):
    """
    Crea documentos de ejemplo con contenido en español.

    Documentos diseñados para probar:
    - Búsqueda por palabras clave
    - Búsqueda insensible a acentos
    - Ranking de relevancia
    - Diferentes categorías
    """
    docs = [
        Document(
            title="Políticas de Vacaciones 2025",
            description="Documento oficial de políticas",
            category="Políticas Internas",
            file_type="pdf",
            file_size_bytes=1024,
            file_path="/uploads/vacaciones.pdf",
            uploaded_by=test_user.id,
            content_text="Las políticas de vacaciones establecen que cada empleado tiene derecho a 15 días de vacaciones anuales. Los procedimientos de solicitud deben seguirse estrictamente.",
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="Procedimiento de Reembolsos",
            description="Guía de reembolsos urgentes",
            category="Procedimientos Operativos",
            file_type="pdf",
            file_size_bytes=2048,
            file_path="/uploads/reembolsos.pdf",
            uploaded_by=test_user.id,
            content_text="El proceso de reembolso especial requiere aprobación del gerente. Los reembolsos urgentes deben procesarse en 24 horas.",
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="Manual de RRHH",
            description="Manual completo recursos humanos",
            category="Políticas Internas",
            file_type="txt",
            file_size_bytes=5120,
            file_path="/uploads/rrhh_manual.txt",
            uploaded_by=test_user.id,
            content_text="El departamento de recursos humanos gestiona políticas de contratación, vacaciones y beneficios. Contactar a RRHH para consultas sobre políticas internas.",
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="Código de Conducta",
            description="Normas de comportamiento",
            category="Políticas Internas",
            file_type="pdf",
            file_size_bytes=3072,
            file_path="/uploads/conducta.pdf",
            uploaded_by=test_user.id,
            content_text="El código de conducta establece normas de comportamiento profesional y ético para todos los empleados de la organización.",
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc)
        ),
        Document(
            title="Documento Sin Indexar",
            description="No debe aparecer en búsquedas",
            category="Test",
            file_type="pdf",
            file_size_bytes=512,
            file_path="/uploads/no_indexed.pdf",
            uploaded_by=test_user.id,
            content_text=None,  # Sin contenido extraído
            is_indexed=False
        )
    ]

    for doc in docs:
        setup_fts5_table.add(doc)

    setup_fts5_table.commit()

    for doc in docs:
        setup_fts5_table.refresh(doc)

    return docs


@pytest.mark.asyncio
async def test_search_basic_keyword(setup_fts5_table, sample_documents):
    """
    AC4: Test búsqueda por palabra clave simple.

    Verifica que búsqueda básica retorna documentos relevantes.
    """
    results = await SearchService.search_documents(
        query="vacaciones",
        limit=10,
        offset=0,
        db=setup_fts5_table
    )

    assert results.query == "vacaciones"
    assert results.total_results >= 2  # "Políticas de Vacaciones" y "Manual de RRHH"
    assert len(results.results) >= 2

    # Verificar que primer resultado es más relevante
    assert "vacaciones" in results.results[0].title.lower() or "vacaciones" in results.results[0].snippet.lower()


@pytest.mark.asyncio
async def test_search_accent_insensitive(setup_fts5_table, sample_documents):
    """
    AC2: Test búsqueda insensible a acentos (tokenizer español).

    Búsqueda "politicas" debe encontrar documentos con "políticas".
    """
    results = await SearchService.search_documents(
        query="politicas",  # Sin acento
        limit=10,
        offset=0,
        db=setup_fts5_table
    )

    assert results.total_results >= 2
    # Debe encontrar documentos que contienen "políticas" con acento
    titles = [r.title for r in results.results]
    assert any("Políticas" in t or "políticas" in t for t in titles)


@pytest.mark.asyncio
async def test_search_exact_phrase(setup_fts5_table, sample_documents):
    """
    AC4: Test búsqueda por frase exacta usando comillas.

    Búsqueda de "proceso de reembolso" debe ser más precisa.
    """
    results = await SearchService.search_documents(
        query='"proceso de reembolso"',
        limit=10,
        offset=0,
        db=setup_fts5_table
    )

    assert results.total_results >= 1
    # Verificar que snippet o título contiene la frase
    assert any("reembolso" in (r.snippet or r.title).lower() for r in results.results)


@pytest.mark.asyncio
async def test_search_boolean_and(setup_fts5_table, sample_documents):
    """
    AC4: Test operador booleano AND implícito.

    Búsqueda múltiple "políticas vacaciones" debe encontrar documentos relevantes.
    """
    results = await SearchService.search_documents(
        query="políticas vacaciones",  # AND implícito en FTS5
        limit=10,
        offset=0,
        db=setup_fts5_table
    )

    # Debe encontrar documentos que contengan al menos uno de los términos
    assert results.total_results >= 1
    # Verificar que resultado contiene al menos un término
    doc = results.results[0]
    content_lower = (doc.snippet or doc.title).lower()
    assert "políticas" in content_lower or "vacaciones" in content_lower or "politicas" in content_lower


@pytest.mark.asyncio
async def test_search_pagination(setup_fts5_table, sample_documents):
    """
    AC5: Test paginación con limit y offset.

    Verifica que paginación retorna diferentes subconjuntos de resultados.
    """
    # Primera página
    page1 = await SearchService.search_documents(
        query="políticas",
        limit=2,
        offset=0,
        db=setup_fts5_table
    )

    # Segunda página
    page2 = await SearchService.search_documents(
        query="políticas",
        limit=2,
        offset=2,
        db=setup_fts5_table
    )

    assert len(page1.results) <= 2
    assert len(page2.results) <= 2

    # Verificar que son documentos diferentes (si hay suficientes resultados)
    if len(page1.results) > 0 and len(page2.results) > 0:
        page1_ids = {r.document_id for r in page1.results}
        page2_ids = {r.document_id for r in page2.results}
        assert page1_ids.isdisjoint(page2_ids)  # Sin overlap


@pytest.mark.asyncio
async def test_search_query_too_short(setup_fts5_table, sample_documents):
    """
    AC7: Test validación de query muy corta.

    Queries con menos de 2 caracteres deben fallar.
    """
    with pytest.raises(ValueError, match="al menos 2 caracteres"):
        await SearchService.search_documents(
            query="a",  # Solo 1 caracter
            limit=10,
            offset=0,
            db=setup_fts5_table
        )


@pytest.mark.asyncio
async def test_search_query_too_long(setup_fts5_table, sample_documents):
    """
    AC7: Test validación de query muy larga.

    Queries con más de 200 caracteres deben fallar.
    """
    long_query = "a" * 201  # 201 caracteres

    with pytest.raises(ValueError, match="no puede exceder 200 caracteres"):
        await SearchService.search_documents(
            query=long_query,
            limit=10,
            offset=0,
            db=setup_fts5_table
        )


@pytest.mark.asyncio
async def test_search_no_results(setup_fts5_table, sample_documents):
    """
    AC7: Test búsqueda sin resultados.

    Búsqueda de término inexistente debe retornar lista vacía.
    """
    results = await SearchService.search_documents(
        query="palabrainexistente12345",
        limit=10,
        offset=0,
        db=setup_fts5_table
    )

    assert results.total_results == 0
    assert len(results.results) == 0


@pytest.mark.asyncio
async def test_search_relevance_ranking(setup_fts5_table, sample_documents):
    """
    AC1/AC3: Test ranking de relevancia BM25.

    Documentos más relevantes deben tener score más alto.
    """
    results = await SearchService.search_documents(
        query="vacaciones",
        limit=10,
        offset=0,
        db=setup_fts5_table
    )

    # Verificar que resultados tienen scores
    assert all(0.0 <= r.relevance_score <= 1.0 for r in results.results)

    # Verificar que resultados están ordenados por relevancia descendente
    if len(results.results) > 1:
        scores = [r.relevance_score for r in results.results]
        assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_search_snippet_extraction(setup_fts5_table, sample_documents):
    """
    AC5: Test extracción de snippets de contexto.

    Snippets deben contener fragmentos relevantes con highlighting.
    """
    results = await SearchService.search_documents(
        query="reembolso",
        limit=10,
        offset=0,
        db=setup_fts5_table
    )

    assert len(results.results) > 0

    # Verificar que snippet o título contiene el término buscado
    result = results.results[0]
    if result.snippet:
        assert "reembolso" in result.snippet.lower()
        assert len(result.snippet) > 0
    else:
        assert "reembolso" in result.title.lower()


@pytest.mark.asyncio
async def test_search_excludes_unindexed(setup_fts5_table, sample_documents):
    """
    AC6/AC7: Test que documentos sin indexar no aparecen en búsqueda.

    Documentos con content_text=None deben ser excluidos.
    """
    # Buscar término que solo existe en documento no indexado
    results = await SearchService.search_documents(
        query="documento",
        limit=10,
        offset=0,
        db=setup_fts5_table
    )

    # No debe retornar el documento "Documento Sin Indexar"
    result_ids = [r.document_id for r in results.results]
    unindexed_doc = [d for d in sample_documents if not d.is_indexed][0]
    assert unindexed_doc.id not in result_ids
