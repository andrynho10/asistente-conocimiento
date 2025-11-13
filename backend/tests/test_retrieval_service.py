"""
Tests for Retrieval Service

Unit tests for the RetrievalService class, covering document retrieval,
query optimization, text normalization, ranking, and edge cases.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlmodel import Session

from app.services.retrieval_service import RetrievalService, SPANISH_SYNONYMS, SPANISH_STOPWORDS
from app.models.document import SearchResult


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def sample_search_results():
    """Sample search results for testing.
    Returns tuples like SQLite Row objects: (document_id, title, category, upload_date, snippet, relevance_score)
    """
    return [
        (1, 'Política de Vacaciones Anuales', 'RRHH', datetime(2025, 11, 13, 10, 30),
         'Los empleados tienen derecho a 15 días hábiles de <mark>vacaciones</mark> anuales...', -1.5),
        (2, 'Guía de Licencias Médicas', 'RRHH', datetime(2025, 11, 12, 15, 45),
         'Para solicitar <mark>licencia</mark> médica, presentar certificado...', -3.2),
        (3, 'Normas de Seguridad Laboral', 'Seguridad', datetime(2025, 11, 11, 9, 20),
         'Las <mark>normas</mark> de seguridad deben ser seguidas por todo el personal...', -5.8)
    ]


class TestRetrievalService:
    """Test cases for RetrievalService."""


class TestRetrieveRelevantDocuments:
    """Test the main retrieve_relevant_documents method."""

    @pytest.mark.asyncio
    async def test_retrieve_documents_success(self, mock_db, sample_search_results):
        """Test successful document retrieval."""
        # Mock database query results
        mock_result = Mock()
        mock_result.fetchall.return_value = sample_search_results
        mock_db.exec.return_value = mock_result

        result = await RetrievalService.retrieve_relevant_documents(
            query="políticas de vacaciones",
            top_k=5,
            db=mock_db
        )

        assert len(result) == 3
        assert result[0].document_id == 1
        assert result[0].title == "Política de Vacaciones Anuales"
        # Normalized from -1.5: normalized = (-1.5 - (-5.8)) / ((-1.5) - (-5.8)) = 4.3/4.3 = 1.0
        assert result[0].relevance_score == 1.0

        # Check that database was queried at least once
        assert mock_db.exec.call_count >= 1

    @pytest.mark.asyncio
    async def test_retrieve_documents_empty_query(self, mock_db):
        """Test retrieval with empty query returns empty list."""
        result = await RetrievalService.retrieve_relevant_documents(
            query="",
            top_k=3,
            db=mock_db
        )

        assert result == []
        assert mock_db.exec.call_count == 0

    @pytest.mark.asyncio
    async def test_retrieve_documents_short_query(self, mock_db):
        """Test retrieval with short query returns empty list."""
        result = await RetrievalService.retrieve_relevant_documents(
            query="a",
            top_k=3,
            db=mock_db
        )

        assert result == []
        assert mock_db.exec.call_count == 0

    @pytest.mark.asyncio
    async def test_retrieve_documents_no_results(self, mock_db):
        """Test retrieval with no matching documents."""
        # Mock empty query results
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.exec.return_value = mock_result

        # Mock count query returning 0
        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = [0]
        mock_db.exec.side_effect = [mock_result, mock_count_result]

        result = await RetrievalService.retrieve_relevant_documents(
            query="documento inexistente",
            top_k=3,
            db=mock_db
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_documents_low_relevance_filtering(self, mock_db):
        """Test filtering out low relevance documents (< 0.1 score)."""
        # Mock results with very low relevance
        low_relevance_results = [
            {
                'document_id': 1,
                'title': 'Documento Irrelevante',
                'category': 'Otros',
                'upload_date': datetime(2025, 11, 13, 10, 30),
                'snippet': 'Contenido no relevante...',
                'relevance_score': -10.0  # Very low relevance
            }
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = low_relevance_results
        mock_db.exec.return_value = mock_result

        # Mock count query
        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = [1]
        mock_db.exec.side_effect = [mock_result, mock_count_result]

        result = await RetrievalService.retrieve_relevant_documents(
            query="término muy específico",
            top_k=5,
            db=mock_db
        )

        # Should be filtered out due to low relevance (< 0.1)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_retrieve_documents_invalid_top_k(self, mock_db):
        """Test retrieval with invalid top_k parameter."""
        with pytest.raises(ValueError, match="top_k debe estar entre 1 y 10"):
            await RetrievalService.retrieve_relevant_documents(
                query="test query",
                top_k=0,
                db=mock_db
            )

        with pytest.raises(ValueError, match="top_k debe estar entre 1 y 10"):
            await RetrievalService.retrieve_relevant_documents(
                query="test query",
                top_k=15,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_retrieve_documents_database_error(self, mock_db):
        """Test retrieval with database error."""
        mock_db.exec.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Error en retrieval de documentos"):
            await RetrievalService.retrieve_relevant_documents(
                query="test query",
                top_k=3,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_retrieve_documents_score_normalization(self, mock_db):
        """Test proper score normalization from BM25 to 0.0-1.0 scale."""
        # Mock results with various BM25 scores
        varied_results = [
            {'document_id': 1, 'title': 'Doc1', 'category': 'Test', 'upload_date': datetime.now(), 'snippet': 'snippet1', 'relevance_score': -1.0},
            {'document_id': 2, 'title': 'Doc2', 'category': 'Test', 'upload_date': datetime.now(), 'snippet': 'snippet2', 'relevance_score': -3.0},
            {'document_id': 3, 'title': 'Doc3', 'category': 'Test', 'upload_date': datetime.now(), 'snippet': 'snippet3', 'relevance_score': -5.0}
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = varied_results
        mock_db.exec.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = [3]
        mock_db.exec.side_effect = [mock_result, mock_count_result]

        result = await RetrievalService.retrieve_relevant_documents(
            query="test query",
            top_k=3,
            db=mock_db
        )

        # Check normalization (BM25: -1.0 should become 1.0, -5.0 should become 0.0)
        scores = [doc.relevance_score for doc in result]
        assert max(scores) == 1.0  # Best score should be 1.0
        assert min(scores) == 0.0  # Worst score should be 0.0
        assert all(0.0 <= score <= 1.0 for score in scores)  # All scores in valid range

    @pytest.mark.asyncio
    async def test_retrieve_documents_with_default_top_k(self, mock_db):
        """Test retrieval with default top_k parameter."""
        # Mock results
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.exec.return_value = mock_result

        # Call with default top_k (should be 3)
        result = await RetrievalService.retrieve_relevant_documents(
            query="test query",
            db=mock_db  # No top_k specified
        )

        # Verify that exec was called (indicating the query was executed)
        assert mock_db.exec.call_count >= 1  # At least main query
        # The default top_k=3 should be used internally
        assert result == []  # No results found


class TestQueryOptimization:
    """Test query optimization methods."""

    def test_optimize_query_simple(self):
        """Test simple query optimization."""
        result = RetrievalService._optimize_query("políticas de vacaciones")

        # Should include normalized terms and synonyms
        assert "politicas" in result  # Normalized (no accent, plural)
        assert "vacacion" in result  # Normalized (no accent)
        assert "OR" in result
        # Should include synonyms for vacaciones (descanso, receso, licencia)
        assert "descanso" in result
        assert "licencia" in result

    def test_optimize_query_with_synonyms(self):
        """Test query optimization with synonym expansion."""
        result = RetrievalService._optimize_query("empleado")

        # Should include employee synonyms
        assert "empleado" in result
        assert "trabajador" in result
        assert "colaborador" in result

    def test_optimize_query_stopwords_filtering(self):
        """Test that stopwords are filtered out."""
        result = RetrievalService._optimize_query("el la y los pero que de")

        # When all terms are stopwords, should return empty string
        # (no meaningful terms to search for)
        assert result == ""  # All stopwords, returns empty query

    def test_optimize_query_mixed_terms(self):
        """Test optimization with mix of meaningful terms and stopwords."""
        result = RetrievalService._optimize_query("el empleado de la empresa")

        # Should include meaningful terms but not stopwords
        assert "empleado" in result
        assert "empresa" in result
        assert "trabajador" in result  # synonym for empleado
        assert "organización" in result  # synonym for empresa

    def test_optimize_query_limiting_expansion(self):
        """Test that query expansion is limited to prevent overloading."""
        # Create a query that would generate many synonyms
        result = RetrievalService._optimize_query("política empleado")

        # Should not be excessively long (limit to ~8 unique terms)
        unique_terms = result.split(" OR ")
        assert len(unique_terms) <= 8

    def test_optimize_query_single_term(self):
        """Test optimization with single meaningful term."""
        result = RetrievalService._optimize_query("salario")

        # Should include term and its synonyms
        assert "salario" in result
        assert "sueldo" in result
        assert "remuneración" in result

    def test_optimize_query_empty_string(self):
        """Test optimization with empty string."""
        result = RetrievalService._optimize_query("")

        assert result == ""

    def test_optimize_query_with_special_characters(self):
        """Test optimization handling special characters."""
        result = RetrievalService._optimize_query("¿políticas de RRHH?")

        # Should handle and clean special characters
        assert "politicas" in result  # Normalized (no accent)
        assert "rrhh" in result


class TestTextNormalization:
    """Test text normalization methods."""

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        result = RetrievalService._normalize_text("Políticas de RRHH")

        assert result == "politicas de rrhh"

    def test_normalize_text_with_accents(self):
        """Test normalization removes diacritics."""
        result = RetrievalService._normalize_text("¡Atención! Seguridad y Evaluación")

        assert result == "atencion seguridad y evaluacion"

    def test_normalize_text_with_punctuation(self):
        """Test normalization handles punctuation."""
        result = RetrievalService._normalize_text("¿Cómo funciona? ¡Bien!")

        # Should replace punctuation with spaces and normalize
        assert "como funciona" in result
        assert "bien" in result

    def test_normalize_text_multiple_spaces(self):
        """Test normalization handles multiple spaces."""
        result = RetrievalService._normalize_text("texto    con     múltiples     espacios")

        assert result == "texto con multiples espacios"

    def test_normalize_text_with_numbers(self):
        """Test normalization preserves numbers."""
        result = RetrievalService._normalize_text("Política 2023 para empleados")

        assert "politica" in result
        assert "2023" in result
        assert "empleados" in result

    def test_normalize_text_empty_string(self):
        """Test normalization with empty string."""
        result = RetrievalService._normalize_text("")

        assert result == ""

    def test_normalize_text_whitespace_only(self):
        """Test normalization with whitespace only."""
        result = RetrievalService._normalize_text("   \t\n   ")

        assert result == ""


class TestSpanishStopwords:
    """Test Spanish stopwords functionality."""

    def test_stopwords_coverage(self):
        """Test that common Spanish stopwords are included."""
        from app.services.retrieval_service import SPANISH_STOPWORDS

        # Test coverage of common stopwords
        common_stopwords = ['el', 'la', 'los', 'las', 'de', 'del', 'en', 'con', 'por', 'para', 'y', 'o', 'que', 'como']

        for word in common_stopwords:
            assert word in SPANISH_STOPWORDS

    def test_stopwords_case_insensitive(self):
        """Test that stopwords work case-insensitively."""
        from app.services.retrieval_service import SPANISH_STOPWORDS

        # Should be lowercase
        for word in SPANISH_STOPWORDS:
            assert word == word.lower()

    def test_stopwords_not_in_normalization(self):
        """Test that stopwords are properly filtered during normalization."""
        # Use a query with only stopwords
        result = RetrievalService._optimize_query("el la y los")

        # Should result in empty or minimal query
        assert len(result.strip()) == 0 or len(result.strip().split()) <= 1


class TestSpanishSynonyms:
    """Test Spanish synonyms functionality."""

    def test_synonyms_coverage(self):
        """Test that common business terms have synonyms."""
        from app.services.retrieval_service import SPANISH_SYNONYMS

        # Test key business terms have synonyms
        key_terms = ['política', 'empleado', 'empresa', 'trabajo', 'salario']

        for term in key_terms:
            assert term in SPANISH_SYNONYMS
            assert len(SPANISH_SYNONYMS[term]) >= 1

    def test_synonyms_quality(self):
        """Test that synonyms are relevant and in Spanish."""
        from app.services.retrieval_service import SPANISH_SYNONYMS

        # Check that synonyms are relevant
        assert 'trabajador' in SPANISH_SYNONYMS['empleado']
        assert 'organización' in SPANISH_SYNONYMS['empresa']
        assert 'remuneración' in SPANISH_SYNONYMS['salario']

    def test_synonyms_in_optimization(self):
        """Test that synonyms are actually used in query optimization."""
        result = RetrievalService._optimize_query("empleado")

        # Should include original term and at least one synonym
        assert "empleado" in result
        assert any(synonym in result for synonym in SPANISH_SYNONYMS['empleado'])


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_db_error(self, mock_db):
        """Test graceful degradation when database has errors."""
        mock_db.exec.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Error en retrieval de documentos"):
            await RetrievalService.retrieve_relevant_documents(
                query="test",
                top_k=3,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_logging_on_retrieval_operations(self, mock_db, caplog):
        """Test that retrieval operations are properly logged."""
        import logging

        # Set up logging capture
        caplog.set_level(logging.INFO)

        # Mock successful retrieval
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.exec.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = [0]
        mock_db.exec.side_effect = [mock_result, mock_count_result]

        await RetrievalService.retrieve_relevant_documents(
            query="test query",
            top_k=3,
            db=mock_db
        )

        # Check that operation was logged
        assert "retrieval_completed" in caplog.text

    @pytest.mark.asyncio
    async def test_error_logging_on_failure(self, mock_db, caplog):
        """Test that errors are properly logged."""
        import logging

        caplog.set_level(logging.ERROR)

        mock_db.exec.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await RetrievalService.retrieve_relevant_documents(
                query="test query",
                top_k=3,
                db=mock_db
            )

        # Check that error was logged
        assert "retrieval_error" in caplog.text


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_single_result_normalization(self, mock_db):
        """Test score normalization with single result."""
        single_result = [
            {
                'document_id': 1,
                'title': 'Single Document',
                'category': 'Test',
                'upload_date': datetime.now(),
                'snippet': 'Single snippet',
                'relevance_score': -2.5
            }
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = single_result
        mock_db.exec.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = [1]
        mock_db.exec.side_effect = [mock_result, mock_count_result]

        result = await RetrievalService.retrieve_relevant_documents(
            query="test",
            top_k=3,
            db=mock_db
        )

        # Single result should get score 1.0
        assert len(result) == 1
        assert result[0].relevance_score == 1.0

    @pytest.mark.asyncio
    async def test_identical_scores_normalization(self, mock_db):
        """Test normalization when all documents have identical scores."""
        identical_results = [
            {'document_id': 1, 'title': 'Doc1', 'category': 'Test', 'upload_date': datetime.now(), 'snippet': 'sn1', 'relevance_score': -2.0},
            {'document_id': 2, 'title': 'Doc2', 'category': 'Test', 'upload_date': datetime.now(), 'snippet': 'sn2', 'relevance_score': -2.0},
            {'document_id': 3, 'title': 'Doc3', 'category': 'Test', 'upload_date': datetime.now(), 'snippet': 'sn3', 'relevance_score': -2.0}
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = identical_results
        mock_db.exec.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = [3]
        mock_db.exec.side_effect = [mock_result, mock_count_result]

        result = await RetrievalService.retrieve_relevant_documents(
            query="test",
            top_k=3,
            db=mock_db
        )

        # All should get score 1.0 when scores are identical
        scores = [doc.relevance_score for doc in result]
        assert all(score == 1.0 for score in scores)

    @pytest.mark.asyncio
    async def test_very_long_query(self, mock_db):
        """Test handling of very long queries."""
        long_query = "política " * 50  # Very long query

        # Mock empty results
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.exec.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = [0]
        mock_db.exec.side_effect = [mock_result, mock_count_result]

        # Should handle gracefully without errors
        result = await RetrievalService.retrieve_relevant_documents(
            query=long_query,
            top_k=3,
            db=mock_db
        )

        assert result == []

    def test_optimize_query_unicode_characters(self):
        """Test query optimization with various Unicode characters."""
        unicode_queries = [
            "café y té",
            "niño y niña",
            "corazón y amor",
            "México y Argentina"
        ]

        for query in unicode_queries:
            result = RetrievalService._optimize_query(query)

            # Should not crash and should produce valid output
            assert isinstance(result, str)
            assert len(result) > 0


class TestIntegration:
    """Integration tests for retrieval service."""

    @pytest.mark.asyncio
    async def test_end_to_end_retrieval_flow(self, mock_db):
        """Test complete retrieval flow from query to results."""
        # Mock realistic database response
        realistic_results = [
            {
                'document_id': 1,
                'title': 'Política de Vacaciones Anuales',
                'category': 'RRHH',
                'upload_date': datetime(2025, 11, 13, 10, 30),
                'snippet': 'Los empleados tienen derecho a 15 días hábiles de <mark>vacaciones</mark> anuales...',
                'relevance_score': -1.8
            },
            {
                'document_id': 2,
                'title': 'Procedimiento de Solicitud de Licencias',
                'category': 'RRHH',
                'upload_date': datetime(2025, 11, 12, 15, 45),
                'snippet': 'Para solicitar <mark>licencia</mark>, completar formulario...',
                'relevance_score': -4.2
            }
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = realistic_results
        mock_db.exec.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = [2]
        mock_db.exec.side_effect = [mock_result, mock_count_result]

        # Perform retrieval
        result = await RetrievalService.retrieve_relevant_documents(
            query="vacaciones y licencias",
            top_k=5,
            db=mock_db
        )

        # Verify complete flow
        assert len(result) == 2
        assert result[0].document_id == 1
        assert result[0].relevance_score > result[1].relevance_score  # Better score first
        assert all(0.0 <= doc.relevance_score <= 1.0 for doc in result)
        assert all(doc.snippet for doc in result)
        assert all(doc.upload_date for doc in result)


@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return {
        'hr_queries': [
            "políticas de vacaciones",
            "procedimientos de contratación",
            "evaluación de desempeño",
            "normas de seguridad laboral"
        ],
        'technical_queries': [
            "configuración de base de datos",
            "implementación de API REST",
            "optimización de consultas SQL",
            "despliegue en producción"
        ],
        'edge_case_queries': [
            "a",  # Too short
            "",   # Empty
            "el la y los pero que de en",  # All stopwords
            "¿Cómo funciona el sistema de gestión de empleados?",  # Long with punctuation
            "política empleado salario trabajo" * 10  # Very long
        ]
    }


class TestRetrievalServiceWithSampleData:
    """Test retrieval service with realistic sample data."""

    @pytest.mark.asyncio
    async def test_hr_domain_queries(self, mock_db, sample_queries):
        """Test retrieval with HR domain queries."""
        for query in sample_queries['hr_queries']:
            # Mock empty results for testing
            mock_result = Mock()
            mock_result.fetchall.return_value = []
            mock_db.exec.return_value = mock_result

            mock_count_result = Mock()
            mock_count_result.fetchone.return_value = [0]
            mock_db.exec.side_effect = [mock_result, mock_count_result]

            result = await RetrievalService.retrieve_relevant_documents(
                query=query,
                top_k=3,
                db=mock_db
            )

            # Should handle HR-specific terminology
            assert isinstance(result, list)

    def test_query_optimization_domain_specific(self, sample_queries):
        """Test that query optimization works well for different domains."""
        # Test HR query optimization
        hr_result = RetrievalService._optimize_query("política de vacaciones")
        assert "politica" in hr_result
        assert "vacacion" in hr_result

        # Test technical query optimization
        tech_result = RetrievalService._optimize_query("implementación de sistema")
        assert "implementacion" in tech_result
        assert "sistema" in tech_result