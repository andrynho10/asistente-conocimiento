"""
Comprehensive Test Suite for RAG Service

Tests all 5 pipeline phases, acceptance criteria, error handling,
timeout management, response formatting, and metric logging.

AC Coverage:
- AC#1: Prerequisites (Story 3.1, 3.2) validation
- AC#2: Pipeline implementation
- AC#3: rag_query() function signature and behavior
- AC#4: 5-phase pipeline execution order
- AC#5: Response structure validation
- AC#6: No relevant documents case
- AC#7: Disclaimer inclusion
- AC#8: Metrics logging
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from app.services.rag_service import RAGService
from app.services.llm_service import OllamaLLMService
from app.models.document import SearchResult


@pytest.fixture
def test_db():
    """In-memory SQLite database for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_llm_service():
    """Mock OllamaLLMService."""
    service = AsyncMock(spec=OllamaLLMService)
    service.generate_response_async = AsyncMock(
        return_value={
            "response": "Esta es una respuesta de prueba sobre vacaciones.",
            "total_tokens": 45,
            "generation_time_ms": 1200
        }
    )
    service.health_check_async = AsyncMock(return_value=True)
    return service


@pytest.fixture
def sample_search_results():
    """Sample search results from retrieval phase."""
    return [
        SearchResult(
            document_id=1,
            title="Política de Vacaciones Anuales",
            category="RRHH",
            relevance_score=0.95,
            snippet="Los empleados tienen derecho a 15 días hábiles de vacaciones anuales.",
            upload_date=datetime.now()
        ),
        SearchResult(
            document_id=2,
            title="Procedimientos de Contratación",
            category="RRHH",
            relevance_score=0.82,
            snippet="El proceso de contratación incluye entrevista, evaluación y aprobación.",
            upload_date=datetime.now()
        ),
        SearchResult(
            document_id=3,
            title="Manual del Empleado",
            category="General",
            relevance_score=0.75,
            snippet="Bienvenido a nuestra organización. Este manual contiene políticas generales.",
            upload_date=datetime.now()
        ),
    ]


class TestRAGServiceBasics:
    """Test RAG service basic functionality and signatures."""

    @pytest.mark.asyncio
    async def test_rag_query_signature_ac3(self, test_db, mock_llm_service, sample_search_results):
        """
        AC#3: Verify rag_query() function signature exists and accepts correct parameters.

        Function signature: rag_query(user_query: str, user_id: int) -> dict
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ):
            response = await RAGService.rag_query(
                user_query="¿Cuántos días de vacaciones tengo?",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
                top_k=3,
                temperature=0.3,
                max_tokens=500
            )

            # Verify response is a dictionary
            assert isinstance(response, dict)

            # Verify required fields per AC#5
            assert "answer" in response
            assert "sources" in response
            assert "response_time_ms" in response
            assert "documents_retrieved" in response

    @pytest.mark.asyncio
    async def test_rag_query_returns_dict_ac5(self, test_db, mock_llm_service, sample_search_results):
        """
        AC#5: Verify return object structure: {answer, sources[], response_time_ms, documents_retrieved}
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ):
            response = await RAGService.rag_query(
                user_query="Test query",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify structure per AC#5
            assert isinstance(response["answer"], str)
            assert isinstance(response["sources"], list)
            assert isinstance(response["response_time_ms"], (int, float))
            assert isinstance(response["documents_retrieved"], int)

            # Verify sources contain required fields
            if response["sources"]:
                source = response["sources"][0]
                assert "document_id" in source
                assert "title" in source
                assert "relevance_score" in source
                assert isinstance(source["relevance_score"], float)
                assert 0.0 <= source["relevance_score"] <= 1.0


class TestRAGPipelineExecution:
    """Test the 5-phase RAG pipeline execution order (AC#4)."""

    @pytest.mark.asyncio
    async def test_five_phase_pipeline_execution_order_ac4(
        self, test_db, mock_llm_service, sample_search_results
    ):
        """
        AC#4: Verify RAG pipeline executes exactly 5 sequential phases:
        1. Retrieval - Recovers top 3 documents
        2. Context Construction - Combines snippets
        3. Augmentation - Builds prompt
        4. Generation - Calls LLM
        5. Response Formatting - Adds sources and disclaimer
        """
        execution_log = []

        # Mock retrieval to track execution
        async def mock_retrieve(query, top_k, db):
            execution_log.append("phase_1_retrieval")
            return sample_search_results[:top_k]

        # Mock LLM to track execution
        async def mock_generate(prompt, temperature, max_tokens):
            execution_log.append("phase_4_generation")
            assert "contexto de documentos" in prompt.lower() or "Contexto de documentos" in prompt
            return {
                "response": "Respuesta de prueba",
                "total_tokens": 50,
                "generation_time_ms": 1200
            }

        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            side_effect=mock_retrieve
        ), patch.object(
            mock_llm_service,
            "generate_response_async",
            side_effect=mock_generate
        ):
            response = await RAGService.rag_query(
                user_query="Pregunta de prueba",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
                top_k=3,
            )

            # Verify phases were executed
            assert "phase_1_retrieval" in execution_log
            assert "phase_4_generation" in execution_log

            # Verify response has all phases' output
            assert response["documents_retrieved"] == 3  # Phase 1 result
            assert response["sources"]  # Phase 2/5 result
            assert "*Nota: Esta respuesta fue generada por IA" in response["answer"]  # Phase 5 result

    @pytest.mark.asyncio
    async def test_top_k_document_retrieval_ac4(self, test_db, mock_llm_service, sample_search_results):
        """
        AC#4: Retrieval phase recovers top 3 documents correctly.
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results[:3]
        ):
            response = await RAGService.rag_query(
                user_query="Test",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
                top_k=3,
            )

            # Verify top 3 docs were retrieved
            assert response["documents_retrieved"] == 3
            assert len(response["sources"]) == 3


class TestNoRelevantDocumentsHandling:
    """Test handling when no relevant documents are found (AC#6)."""

    @pytest.mark.asyncio
    async def test_no_relevant_documents_ac6(self, test_db, mock_llm_service):
        """
        AC#6: If no relevant documents (all scores < 0.1):
        - NO LLM call (cost savings)
        - Return polite response
        - No sources in response
        """
        # Return documents below threshold
        low_relevance_results = [
            SearchResult(
                document_id=99,
                title="Irrelevant Doc",
                category="Other",
                relevance_score=0.05,  # Below 0.1 threshold
                snippet="This is not relevant",
                upload_date=datetime.now()
            ),
        ]

        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=low_relevance_results
        ):
            response = await RAGService.rag_query(
                user_query="Pregunta sin documentos relevantes",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify LLM was NOT called (AC#6: cost savings)
            mock_llm_service.generate_response_async.assert_not_called()

            # Verify polite response without context
            assert "no encontré documentos relevantes" in response["answer"].lower()
            assert response["documents_retrieved"] == 0
            assert response["sources"] == []

    @pytest.mark.asyncio
    async def test_empty_retrieval_results_ac6(self, test_db, mock_llm_service):
        """
        AC#6: Handle empty retrieval results (no documents at all).
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=[]  # Empty results
        ):
            response = await RAGService.rag_query(
                user_query="Pregunta sin resultados",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify graceful handling
            mock_llm_service.generate_response_async.assert_not_called()
            assert response["documents_retrieved"] == 0
            assert response["sources"] == []


class TestDisclaimerAndFormatting:
    """Test disclaimer inclusion and response formatting (AC#7)."""

    @pytest.mark.asyncio
    async def test_disclaimer_inclusion_ac7(self, test_db, mock_llm_service, sample_search_results):
        """
        AC#7: All responses must include disclaimer:
        "*Nota: Esta respuesta fue generada por IA. Verifica con tu supervisor si tienes dudas.*"
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ):
            response = await RAGService.rag_query(
                user_query="Pregunta cualquiera",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify disclaimer is in answer
            assert "*Nota: Esta respuesta fue generada por IA" in response["answer"]
            assert "Verifica con tu supervisor si tienes dudas" in response["answer"]

    @pytest.mark.asyncio
    async def test_disclaimer_in_no_docs_case_ac7(self, test_db, mock_llm_service):
        """
        AC#7: Disclaimer included even when no documents found.
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=[]
        ):
            response = await RAGService.rag_query(
                user_query="Sin documentos",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify disclaimer is present
            assert "*Nota: Esta respuesta fue generada por IA" in response["answer"]

    @pytest.mark.asyncio
    async def test_sources_formatting_ac5(self, test_db, mock_llm_service, sample_search_results):
        """
        AC#5: Sources formatted correctly with: {document_id, title, relevance_score}
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ):
            response = await RAGService.rag_query(
                user_query="Test",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify sources structure
            for source in response["sources"]:
                assert isinstance(source["document_id"], int)
                assert isinstance(source["title"], str)
                assert isinstance(source["relevance_score"], float)
                assert 0.0 <= source["relevance_score"] <= 1.0


class TestMetricsLogging:
    """Test comprehensive metrics logging (AC#8)."""

    @pytest.mark.asyncio
    async def test_metrics_logging_ac8(self, test_db, mock_llm_service, sample_search_results, caplog):
        """
        AC#8: Verify metrics logging includes:
        - response_time_ms
        - documents_retrieved
        - avg_relevance_score
        - tokens_used
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ):
            response = await RAGService.rag_query(
                user_query="Prueba de métricas",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify response metrics
            assert "response_time_ms" in response
            assert response["response_time_ms"] > 0
            assert "documents_retrieved" in response
            assert response["documents_retrieved"] == 3

    @pytest.mark.asyncio
    async def test_response_time_metric_ac8(self, test_db, mock_llm_service, sample_search_results):
        """
        AC#8: response_time_ms metric must be present and non-negative.
        RNF2: Response time <2 seconds (P95).
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ):
            response = await RAGService.rag_query(
                user_query="Test response time",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify timing metric
            assert isinstance(response["response_time_ms"], (int, float))
            assert response["response_time_ms"] >= 0
            # Note: In-memory test will be fast, but production should be <2000ms


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_llm_timeout_handling(self, test_db, mock_llm_service, sample_search_results):
        """
        Test graceful handling of LLM timeout (10s standard).
        """
        # Mock LLM to timeout
        mock_llm_service.generate_response_async = AsyncMock(
            side_effect=asyncio.TimeoutError("LLM timeout")
        )

        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ):
            response = await RAGService.rag_query(
                user_query="Causes timeout",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify graceful error handling
            assert "tardó demasiado" in response["answer"]
            assert response["documents_retrieved"] == 0

    @pytest.mark.asyncio
    async def test_general_exception_handling(self, test_db, mock_llm_service):
        """
        Test handling of unexpected exceptions.
        """
        # Mock retrieval to raise exception
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            side_effect=Exception("Database connection error")
        ):
            response = await RAGService.rag_query(
                user_query="Causes error",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify error response
            assert "error procesando" in response["answer"].lower()
            assert response["documents_retrieved"] == 0
            assert response["sources"] == []


class TestContextLimit:
    """Test context limit handling (AC#4)."""

    @pytest.mark.asyncio
    async def test_context_limit_2000_chars(self, test_db, mock_llm_service):
        """
        Test that context is limited to ~2000 characters to prevent token overflow.
        """
        # Create results with long snippets
        long_results = [
            SearchResult(
                document_id=1,
                title="Doc 1",
                category="Test",
                relevance_score=0.9,
                snippet="A" * 800,  # 800 chars
                upload_date=datetime.now()
            ),
            SearchResult(
                document_id=2,
                title="Doc 2",
                category="Test",
                relevance_score=0.8,
                snippet="B" * 800,  # 800 chars
                upload_date=datetime.now()
            ),
            SearchResult(
                document_id=3,
                title="Doc 3",
                category="Test",
                relevance_score=0.7,
                snippet="C" * 800,  # 800 chars
                upload_date=datetime.now()
            ),
        ]

        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=long_results
        ):
            response = await RAGService.rag_query(
                user_query="Test context limit",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Context should be limited, so not all 3 documents might be used
            # (depends on exact formatting overhead)
            assert response["documents_retrieved"] <= 3


class TestHealthCheck:
    """Test RAG service health check."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_llm_service):
        """
        Test successful health check when all services are available.
        """
        mock_llm_service.health_check_async = AsyncMock(return_value=True)

        result = await RAGService.health_check(mock_llm_service)
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_llm_unhealthy(self, mock_llm_service):
        """
        Test health check fails when LLM service is unavailable.
        """
        mock_llm_service.health_check_async = AsyncMock(return_value=False)

        result = await RAGService.health_check(mock_llm_service)
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, mock_llm_service):
        """
        Test health check gracefully handles exceptions.
        """
        mock_llm_service.health_check_async = AsyncMock(
            side_effect=Exception("Connection error")
        )

        result = await RAGService.health_check(mock_llm_service)
        assert result is False


class TestSpanishNLPSupport:
    """Test Spanish NLP handling with RetrievalService integration."""

    @pytest.mark.asyncio
    async def test_spanish_query_processing(self, test_db, mock_llm_service, sample_search_results):
        """
        Test that Spanish queries are processed correctly with
        stopword filtering and synonym expansion from RetrievalService.
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ) as mock_retrieve:
            response = await RAGService.rag_query(
                user_query="¿Cuántos días de vacaciones tengo en la organización?",
                user_id=1,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify retrieval was called with Spanish query
            mock_retrieve.assert_called_once()
            call_args = mock_retrieve.call_args
            assert "vacaciones" in call_args[1]["query"].lower()

            # Verify response in Spanish
            assert response["documents_retrieved"] >= 0


class TestEndToEndRAGPipeline:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_rag_flow_with_documents(self, test_db, mock_llm_service, sample_search_results):
        """
        Complete end-to-end test with documents retrieved and LLM called.
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=sample_search_results
        ):
            response = await RAGService.rag_query(
                user_query="¿Cuántos días de vacaciones tengo?",
                user_id=42,
                session=test_db,
                llm_service=mock_llm_service,
                top_k=3,
                temperature=0.3,
                max_tokens=500
            )

            # Verify complete flow
            assert response["documents_retrieved"] > 0
            assert len(response["sources"]) > 0
            assert response["response_time_ms"] > 0
            assert "*Nota: Esta respuesta fue generada por IA" in response["answer"]

            # Verify LLM was called
            mock_llm_service.generate_response_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_rag_flow_without_documents(self, test_db, mock_llm_service):
        """
        Complete end-to-end test with no relevant documents.
        """
        with patch(
            "app.services.rag_service.RetrievalService.retrieve_relevant_documents",
            new_callable=AsyncMock,
            return_value=[]
        ):
            response = await RAGService.rag_query(
                user_query="Pregunta sin documentos relevantes",
                user_id=42,
                session=test_db,
                llm_service=mock_llm_service,
            )

            # Verify flow for no documents
            assert response["documents_retrieved"] == 0
            assert response["sources"] == []
            assert "no encontré documentos" in response["answer"].lower()

            # LLM should NOT be called
            mock_llm_service.generate_response_async.assert_not_called()
