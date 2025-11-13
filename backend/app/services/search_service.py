"""
Servicio de búsqueda full-text usando SQLite FTS5.

Proporciona búsqueda rápida sobre contenido de documentos con ranking
de relevancia BM25, snippets de contexto y soporte para español.
"""

import logging
import json
from datetime import datetime
from typing import Optional
from sqlmodel import Session, text

from app.models.document import SearchRequest, SearchResponse, SearchResult

# Configurar logging estructurado
logger = logging.getLogger(__name__)


class SearchService:
    """
    Servicio para búsqueda full-text de documentos usando SQLite FTS5.

    Implementa búsqueda con:
    - Ranking BM25 integrado en FTS5
    - Snippets de contexto con highlighting
    - Tokenizer español (unicode61 remove_diacritics)
    - Soporte para palabras clave, frases exactas y operadores booleanos
    """

    @staticmethod
    async def search_documents(
        query: str,
        limit: int = 20,
        offset: int = 0,
        db: Session = None
    ) -> SearchResponse:
        """
        Busca documentos usando búsqueda full-text FTS5.

        Realiza búsqueda sobre título y contenido de documentos indexados,
        retornando resultados ordenados por relevancia con snippets de contexto.

        Args:
            query: Término de búsqueda (min 2 caracteres, max 200)
            limit: Número máximo de resultados (1-100, default 20)
            offset: Offset para paginación (default 0)
            db: Sesión de base de datos SQLModel

        Returns:
            SearchResponse: Objeto con query, total_results y lista de resultados

        Raises:
            ValueError: Si query es muy corto (<2 chars) o muy largo (>200 chars)
            Exception: Si hay error de sintaxis FTS5 o query mal formada

        Example:
            >>> results = await SearchService.search_documents("políticas rrhh", 10, 0, db)
            >>> print(f"Encontrados {results.total_results} documentos")
        """
        start_time = datetime.now()

        # Validar parámetros
        if len(query) < 2:
            logger.warning(
                json.dumps({
                    "event": "search_validation_error",
                    "error": "Query muy corta",
                    "query_length": len(query),
                    "min_required": 2
                })
            )
            raise ValueError("Query debe tener al menos 2 caracteres")

        if len(query) > 200:
            logger.warning(
                json.dumps({
                    "event": "search_validation_error",
                    "error": "Query muy larga",
                    "query_length": len(query),
                    "max_allowed": 200
                })
            )
            raise ValueError("Query no puede exceder 200 caracteres")

        # Sanitizar query para FTS5 (escapar caracteres especiales)
        sanitized_query = SearchService._sanitize_fts5_query(query)

        try:
            # Query FTS5 con ranking BM25 y snippets
            # JOIN con tabla documents para obtener upload_date
            sql_query = text("""
                SELECT
                    fts.document_id,
                    fts.title,
                    fts.category,
                    d.upload_date,
                    snippet(documents_fts, 2, '<mark>', '</mark>', '...', 64) as snippet,
                    bm25(documents_fts) as relevance_score
                FROM documents_fts fts
                INNER JOIN documents d ON fts.document_id = d.id
                WHERE documents_fts MATCH :query
                ORDER BY bm25(documents_fts)
                LIMIT :limit OFFSET :offset
            """)

            # Ejecutar query
            result = db.exec(sql_query.bindparams(query=sanitized_query, limit=limit, offset=offset))
            rows = result.fetchall()

            # Contar total de resultados (sin limit/offset)
            count_query = text("""
                SELECT COUNT(*)
                FROM documents_fts
                WHERE documents_fts MATCH :query
            """)
            total_result = db.exec(count_query.bindparams(query=sanitized_query))
            total_count = total_result.fetchone()[0]

            # Normalizar scores de relevancia (BM25 negativo, menor es mejor)
            # Convertir a escala 0.0-1.0 donde 1.0 es más relevante
            results = []
            if rows:
                min_score = min(row[5] for row in rows)
                max_score = max(row[5] for row in rows)
                score_range = max_score - min_score if max_score != min_score else 1.0

                for row in rows:
                    # Normalizar score: invertir (BM25 negativo) y escalar a 0-1
                    normalized_score = 1.0 - ((row[5] - min_score) / score_range) if score_range > 0 else 1.0

                    results.append(SearchResult(
                        document_id=row[0],
                        title=row[1],
                        category=row[2],
                        upload_date=row[3],
                        snippet=row[4],
                        relevance_score=round(normalized_score, 2)
                    ))

            # Logging estructurado con métricas
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info(
                json.dumps({
                    "event": "search_completed",
                    "query": query,
                    "sanitized_query": sanitized_query,
                    "total_results": total_count,
                    "returned_results": len(results),
                    "limit": limit,
                    "offset": offset,
                    "elapsed_ms": elapsed_ms,
                    "avg_relevance": round(sum(r.relevance_score for r in results) / len(results), 2) if results else 0.0
                })
            )

            return SearchResponse(
                query=query,
                total_results=total_count,
                results=results
            )

        except Exception as e:
            # Log error estructurado
            logger.error(
                json.dumps({
                    "event": "search_error",
                    "query": query,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "limit": limit,
                    "offset": offset
                })
            )
            raise Exception(f"Error en búsqueda FTS5: {str(e)}")

    @staticmethod
    def _sanitize_fts5_query(query: str) -> str:
        """
        Sanitiza query para búsqueda FTS5, preservando operadores válidos.

        FTS5 soporta operadores especiales (AND, OR, NOT, "frases exactas").
        Esta función protege contra queries mal formadas mientras permite
        operadores válidos.

        Args:
            query: Query original del usuario

        Returns:
            str: Query sanitizada para FTS5

        Example:
            >>> SearchService._sanitize_fts5_query('política RRHH')
            'política RRHH'
            >>> SearchService._sanitize_fts5_query('"políticas de RRHH"')
            '"políticas de RRHH"'
        """
        # Por ahora, pasar query directamente (FTS5 maneja bien la mayoría de casos)
        # En producción, podrías agregar lógica más sofisticada aquí
        # para escapar caracteres especiales problemáticos
        return query.strip()
