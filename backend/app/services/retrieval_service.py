"""
Servicio de Retrieval para búsqueda inteligente de documentos relevantes.

Proporciona recuperación optimizada de documentos para consultas IA,
con expansión de consultas, normalización de texto y ranking avanzado.
"""

import logging
import json
import re
import unicodedata
from datetime import datetime
from typing import List, Optional, Set
from sqlmodel import Session, text

from app.models.document import SearchResult

# Configurar logging estructurado
logger = logging.getLogger(__name__)

# Stopwords en español para optimización de búsqueda
SPANISH_STOPWORDS = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'en', 'con', 'por',
    'para', 'y', 'o', 'pero', 'mas', 'ni', 'que', 'como', 'cuando', 'donde', 'quien', 'cual',
    'cuyo', 'cuya', 'sus', 'mi', 'tu', 'su', 'nuestro', 'nuestra', 'vuestro', 'vuestra',
    'es', 'son', 'fue', 'fueron', 'ser', 'estar', 'está', 'están', 'han', 'ha', 'había',
    'habían', 'habrá', 'habrán', 'hemos', 'habéis', 'han', 'a', 'ante', 'bajo', 'cabe',
    'contra', 'desde', 'hacia', 'hasta', 'mediante', 'según', 'sin', 'so', 'sobre', 'tras',
    'durante', 'este', 'esta', 'este', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas',
    'aquel', 'aquella', 'aquellos', 'aquellas', 'esto', 'eso', 'aquello', 'muy', 'más',
    'menos', 'mucho', 'poco', 'bastante', 'demasiado', 'también', 'tampoco', 'sí', 'no',
    'solo', 'solamente', 'inclusive', 'incluso', 'aún', 'todavía', 'quizás', 'acaso',
    'tal', 'vez', 'si', 'no', 'además', 'después', 'antes', 'mientras', 'cuanto', 'cuanta'
}

# Sinónimos comunes en español para expansión de consultas
SPANISH_SYNONYMS = {
    'política': ['norma', 'reglamento', 'directriz', 'procedimiento'],
    'empleado': ['trabajador', 'colaborador', 'personal', 'staff', 'funcionario'],
    'empresa': ['organización', 'compañía', 'corporación', 'firma', 'negocio'],
    'trabajo': ['labor', 'tarea', 'actividad', 'ocupación', 'empleo'],
    'salario': ['sueldo', 'remuneración', 'pago', 'ingreso', 'honorarios'],
    'vacaciones': ['descanso', 'receso', 'licencia', 'periodo libre'],
    'capacitación': ['formación', 'entrenamiento', 'aprendizaje', 'curso'],
    'evaluación': ['valoración', 'revisión', 'análisis', 'auditoría'],
    'recurso': ['medio', 'herramienta', 'elemento', 'factor'],
    'documento': ['archivo', 'expediente', 'registro', 'papel'],
    'proceso': ['procedimiento', 'método', 'trámite', 'flujo'],
    'sistema': ['plataforma', 'aplicación', 'software', 'herramienta'],
    'información': ['datos', 'contenido', 'material', 'detalle'],
    'seguridad': ['protección', 'resguardo', 'prevención', 'control'],
    'calidad': ['excelencia', 'estándar', 'nivel', 'cumplimiento'],
    'gestión': ['administración', 'manejo', 'dirección', 'control'],
    'desarrollo': ['crecimiento', 'evolución', 'progreso', 'avance'],
    'implementación': ['aplicación', 'ejecución', 'puesta en marcha'],
    'requerimiento': ['necesidad', 'requisito', 'condición', 'especificación']
}


class RetrievalService:
    """
    Servicio de Retrieval para búsqueda inteligente de documentos.

    Implementa recuperación optimizada con:
    - Expansión de consultas con sinónimos
    - Normalización de texto (lowercase, diacríticos)
    - Filtrado de stopwords español
    - Ranking BM25 avanzado con scores 0.0-1.0
    - Manejo inteligente de consultas sin resultados
    """

    @staticmethod
    async def retrieve_relevant_documents(
        query: str,
        top_k: int = 3,
        db: Session = None
    ) -> List[SearchResult]:
        """
        Recupera los documentos más relevantes para una consulta IA.

        Optimiza la búsqueda con expansión de términos, normalización
        y ranking avanzado para proporcionar contexto preciso al LLM.

        Args:
            query: Consulta del usuario (ej: "políticas de vacaciones")
            top_k: Número de documentos a retornar (default: 3, max: 10)
            db: Sesión de base de datos SQLModel

        Returns:
            List[SearchResult]: Lista de documentos relevantes con scores 0.0-1.0

        Raises:
            ValueError: Si query está vacío o parámetros inválidos
            Exception: Si hay error en búsqueda o base de datos

        Example:
            >>> docs = await RetrievalService.retrieve_relevant_documents(
            ...     "políticas de vacaciones", 5, db
            ... )
            >>> for doc in docs:
            ...     print(f"{doc.title}: {doc.relevance_score}")
        """
        start_time = datetime.now()

        # Validar parámetros
        if not query or len(query.strip()) < 2:
            logger.warning(
                json.dumps({
                    "event": "retrieval_validation_error",
                    "error": "Query muy corta o vacía",
                    "query_length": len(query) if query else 0,
                    "min_required": 2
                })
            )
            return []  # Retornar lista vacía en lugar de error para IA

        if top_k < 1 or top_k > 10:
            raise ValueError("top_k debe estar entre 1 y 10")

        # Optimizar consulta con expansión y normalización
        optimized_query = RetrievalService._optimize_query(query)

        # Si la query optimizada es vacía (solo stopwords), retorna lista vacía
        if not optimized_query or not optimized_query.strip():
            logger.warning(
                json.dumps({
                    "event": "retrieval_validation_error",
                    "error": "Query contiene solo stopwords",
                    "original_query": query,
                    "optimized_query": optimized_query
                })
            )
            return []

        try:
            # Query FTS5 optimizada con ranking BM25
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
                LIMIT :limit
            """)

            # Ejecutar query
            result = db.exec(sql_query.bindparams(query=optimized_query, limit=top_k))
            rows = result.fetchall()

            # Normalizar scores y filtrar por umbral mínimo
            results = []
            if rows:
                # Extraer scores - soportar tanto tuplas como diccionarios
                def get_score(row):
                    if isinstance(row, dict):
                        return row['relevance_score']
                    else:
                        return row[5]

                def get_value(row, index_or_key):
                    if isinstance(rows[0], dict):
                        keys = ['document_id', 'title', 'category', 'upload_date', 'snippet', 'relevance_score']
                        return row[keys[index_or_key]]
                    else:
                        return row[index_or_key]

                # Calcular rango de scores para normalización
                min_score = min(get_score(row) for row in rows)
                max_score = max(get_score(row) for row in rows)
                score_range = max_score - min_score

                # Normalizar todos los documentos primero
                normalized_docs = []
                for row in rows:
                    raw_score = get_score(row)
                    # Normalizar score BM25 a escala 0.0-1.0
                    # Los scores BM25 negativos se normalizan donde el mayor score = 1.0
                    if score_range == 0:
                        # Todos los scores son iguales
                        # Si hay un único documento, normalizarlo a 1.0 (es el mejor match)
                        # PERO si el score es extremadamente bajo, mantenerlo bajo para filtrado
                        if len(rows) == 1:
                            # Documento único
                            if raw_score < -8.0:
                                # Score extremadamente bajo - mantener bajo para filtrado
                                normalized_score = 0.05
                            else:
                                # Score razonable - normalizar a 1.0
                                normalized_score = 1.0
                        else:
                            # Múltiples documentos con scores iguales - todos normalizan a 1.0
                            normalized_score = 1.0
                    else:
                        normalized_score = (raw_score - min_score) / score_range
                    normalized_docs.append((row, normalized_score))

                # Si todos los documentos tienen score < 0.1, retorna lista vacía (AC #6)
                max_normalized_score = max(score for _, score in normalized_docs)
                if max_normalized_score < 0.1:
                    results = []
                else:
                    # De lo contrario, retorna todos los documentos encontrados
                    for row, normalized_score in normalized_docs:
                        # Manejar tuplas y diccionarios
                        if isinstance(row, dict):
                            doc = SearchResult(
                                document_id=row['document_id'],
                                title=row['title'],
                                category=row['category'],
                                upload_date=row['upload_date'],
                                snippet=row['snippet'],
                                relevance_score=round(normalized_score, 3)
                            )
                        else:
                            doc = SearchResult(
                                document_id=row[0],
                                title=row[1],
                                category=row[2],
                                upload_date=row[3],
                                snippet=row[4],
                                relevance_score=round(normalized_score, 3)
                            )
                        results.append(doc)

            # Logging estructurado con métricas
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info(
                json.dumps({
                    "event": "retrieval_completed",
                    "original_query": query,
                    "optimized_query": optimized_query,
                    "documents_found": len(results),
                    "requested_k": top_k,
                    "elapsed_ms": elapsed_ms,
                    "avg_relevance": round(sum(r.relevance_score for r in results) / len(results), 3) if results else 0.0,
                    "min_relevance": round(min(r.relevance_score for r in results), 3) if results else 0.0
                })
            )

            return results

        except Exception as e:
            # Log error estructurado
            logger.error(
                json.dumps({
                    "event": "retrieval_error",
                    "query": query,
                    "optimized_query": optimized_query,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "top_k": top_k
                })
            )
            raise Exception(f"Error en retrieval de documentos: {str(e)}")

    @staticmethod
    def _optimize_query(query: str) -> str:
        """
        Optimiza la consulta con expansión de términos y normalización.

        Aplica técnicas de NLP para mejorar la precisión de búsqueda:
        1. Normalización de texto (lowercase, eliminación de diacríticos)
        2. Expansión con sinónimos
        3. Filtrado de stopwords
        4. Limpieza de caracteres especiales

        Args:
            query: Consulta original del usuario

        Returns:
            str: Consulta optimizada para FTS5

        Example:
            >>> RetrievalService._optimize_query("Políticas de RRHH")
            'política OR regla OR directriz OR empleado OR trabajador'
        """
        # Paso 1: Normalizar texto (lowercase, eliminar diacríticos)
        normalized = RetrievalService._normalize_text(query.lower())

        # Paso 2: Tokenizar y eliminar stopwords
        tokens = [token for token in normalized.split() if token not in SPANISH_STOPWORDS]

        if not tokens:
            return ""  # Si todo son stopwords, retorna query vacía

        # Paso 3: Expansión con sinónimos
        expanded_terms = []
        for token in tokens:
            expanded_terms.append(token)
            # Agregar sinónimos si existen
            if token in SPANISH_SYNONYMS:
                expanded_terms.extend(SPANISH_SYNONYMS[token])

        # Paso 4: Construir query optimizada con operadores OR
        # Esto expande el alcance de búsqueda mientras mantiene relevancia
        if len(expanded_terms) > 1:
            # Limitar expansión para no sobrecargar el query
            unique_terms = list(dict.fromkeys(expanded_terms))[:8]  # Max 8 términos únicos
            optimized_query = " OR ".join(unique_terms)
        else:
            optimized_query = expanded_terms[0]

        return optimized_query

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normaliza texto eliminando diacríticos y caracteres especiales.

        Convierte texto a forma normalizada NFD y elimina caracteres
        de combinación (acentos, diéresis, etc.).

        Args:
            text: Texto a normalizar

        Returns:
            str: Texto normalizado sin diacríticos

        Example:
            >>> RetrievalService._normalize_text("políticas de RRHH")
            'politicas de rrhh'
        """
        # Convertir a minúsculas primero
        text = text.lower()

        # Convertir a NFD (Normalization Form Decomposition)
        # y eliminar caracteres de combinación (acentos, diéresis, etc.)
        normalized = unicodedata.normalize('NFD', text)
        # Mantener solo caracteres básicos ASCII y espacios
        result = re.sub(r'[\u0300-\u036f]', '', normalized)  # Eliminar diacríticos
        result = re.sub(r'[^\w\s]', ' ', result)  # Reemplazar puntuación con espacios
        result = re.sub(r'\s+', ' ', result).strip()  # Normalizar espacios

        return result