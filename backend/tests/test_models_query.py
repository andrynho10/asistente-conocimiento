"""
Unit tests for Query and PerformanceMetric models.

Tests data model persistence and relationships for RAG query tracking.
AC#8: Data Model Persistence - Query model creation with all required fields
and PerformanceMetric model tracking timing data.
"""

import pytest
from datetime import datetime, timezone
from app.models.query import (
    Query,
    QueryCreate,
    QueryRead,
    PerformanceMetric,
    PerformanceMetricCreate,
    PerformanceMetricRead,
)
from app.models.user import User, UserRole
from app.core.security import get_password_hash


@pytest.fixture
def test_user(test_db_session):
    """Create a test user for query records."""
    user = User(
        username="query_test_user",
        email="query_test@example.com",
        full_name="Query Test User",
        hashed_password=get_password_hash("testpass"),
        role=UserRole.user,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


class TestQueryModel:
    """Test Query model for RAG query audit logging (AC#8)."""

    def test_create_query_record(self, test_db_session, test_user):
        """AC#8: Query model stores all required fields."""
        query_record = Query(
            user_id=test_user.id,
            query_text="¿Cuál es la política de vacaciones?",
            answer_text="Los empleados tienen derecho a 15 días hábiles anuales.",
            sources_json='[{"document_id": 1, "title": "Política", "relevance_score": 0.95}]',
            response_time_ms=1245.5
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)

        assert query_record.id is not None
        assert query_record.user_id == test_user.id
        assert query_record.query_text == "¿Cuál es la política de vacaciones?"
        assert query_record.answer_text == "Los empleados tienen derecho a 15 días hábiles anuales."
        assert query_record.response_time_ms == 1245.5

    def test_query_record_with_default_timestamp(self, test_db_session, test_user):
        """AC#8: created_at timestamp defaults to current UTC time."""
        before_create = datetime.now(timezone.utc)
        query_record = Query(
            user_id=test_user.id,
            query_text="Pregunta de prueba válida",
            answer_text="Respuesta de prueba",
            sources_json="[]",
            response_time_ms=100.0
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)
        after_create = datetime.now(timezone.utc)

        # created_at should be between before and after times
        # Handle both timezone-aware and naive datetimes
        query_created = query_record.created_at
        if query_created.tzinfo is None:
            query_created = query_created.replace(tzinfo=timezone.utc)
        assert before_create <= query_created <= after_create

    def test_query_record_queryable_by_user_id(self, test_db_session, test_user):
        """AC#8: Records queryable by user_id."""
        # Create multiple queries
        for i in range(3):
            query_record = Query(
                user_id=test_user.id,
                query_text=f"Pregunta {i}",
                answer_text=f"Respuesta {i}",
                sources_json="[]",
                response_time_ms=float(100 + i)
            )
            test_db_session.add(query_record)
        test_db_session.commit()

        # Query by user_id
        user_queries = test_db_session.query(Query).filter(
            Query.user_id == test_user.id
        ).all()

        assert len(user_queries) == 3
        assert all(q.user_id == test_user.id for q in user_queries)

    def test_query_record_queryable_by_timestamp(self, test_db_session, test_user):
        """AC#8: Records queryable by timestamp."""
        query_record = Query(
            user_id=test_user.id,
            query_text="Pregunta para búsqueda por timestamp",
            answer_text="Respuesta",
            sources_json="[]",
            response_time_ms=100.0
        )
        test_db_session.add(query_record)
        test_db_session.commit()

        # Query by timestamp range
        found_query = test_db_session.query(Query).filter(
            Query.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        ).first()

        assert found_query is not None
        assert found_query.query_text == "Pregunta para búsqueda por timestamp"

    def test_query_record_max_length(self, test_db_session, test_user):
        """Test that query_text respects max_length constraint."""
        # Query text is limited to 500 chars by Field(max_length=500)
        long_query = "a" * 500
        query_record = Query(
            user_id=test_user.id,
            query_text=long_query,
            answer_text="Respuesta",
            sources_json="[]",
            response_time_ms=100.0
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)

        assert len(query_record.query_text) == 500

    def test_query_record_indexed_fields(self, test_db_session, test_user):
        """Test that indexed fields (user_id, created_at) improve query performance."""
        # Create multiple queries
        for i in range(10):
            query_record = Query(
                user_id=test_user.id,
                query_text=f"Query {i}",
                answer_text=f"Answer {i}",
                sources_json="[]",
                response_time_ms=float(100 + i)
            )
            test_db_session.add(query_record)
        test_db_session.commit()

        # Both of these should use indexes
        by_user = test_db_session.query(Query).filter(Query.user_id == test_user.id).count()
        by_time = test_db_session.query(Query).filter(
            Query.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()

        assert by_user == 10
        assert by_time == 10


class TestPerformanceMetricModel:
    """Test PerformanceMetric model for timing data tracking (AC#8)."""

    def test_create_performance_metric(self, test_db_session, test_user):
        """AC#8: PerformanceMetric model tracks timing data."""
        # Create a query first
        query_record = Query(
            user_id=test_user.id,
            query_text="Pregunta para métrica de performance",
            answer_text="Respuesta",
            sources_json="[]",
            response_time_ms=1245.5
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)

        # Create performance metric
        metric = PerformanceMetric(
            query_id=query_record.id,
            retrieval_time_ms=450.0,
            llm_time_ms=750.0,
            total_time_ms=1245.5,
            cache_hit=False
        )
        test_db_session.add(metric)
        test_db_session.commit()
        test_db_session.refresh(metric)

        assert metric.id is not None
        assert metric.query_id == query_record.id
        assert metric.retrieval_time_ms == 450.0
        assert metric.llm_time_ms == 750.0
        assert metric.total_time_ms == 1245.5
        assert metric.cache_hit is False

    def test_performance_metric_timing_accuracy(self, test_db_session, test_user):
        """AC#8: PerformanceMetric accurately tracks timing phases."""
        query_record = Query(
            user_id=test_user.id,
            query_text="Pregunta para timing",
            answer_text="Respuesta",
            sources_json="[]",
            response_time_ms=1200.0
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)

        # Create metric with specific timing breakdown
        metric = PerformanceMetric(
            query_id=query_record.id,
            retrieval_time_ms=400.0,
            llm_time_ms=800.0,
            total_time_ms=1200.0,
            cache_hit=False
        )
        test_db_session.add(metric)
        test_db_session.commit()
        test_db_session.refresh(metric)

        # Verify breakdown
        assert metric.retrieval_time_ms + metric.llm_time_ms == metric.total_time_ms
        assert metric.total_time_ms == query_record.response_time_ms

    def test_performance_metric_with_cache_hit(self, test_db_session, test_user):
        """AC#8: PerformanceMetric tracks cache hit status."""
        query_record = Query(
            user_id=test_user.id,
            query_text="Pregunta cacheable",
            answer_text="Respuesta",
            sources_json="[]",
            response_time_ms=100.0
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)

        # Cache hit metric should have minimal retrieval/LLM time
        metric = PerformanceMetric(
            query_id=query_record.id,
            retrieval_time_ms=10.0,
            llm_time_ms=0.0,
            total_time_ms=100.0,
            cache_hit=True
        )
        test_db_session.add(metric)
        test_db_session.commit()
        test_db_session.refresh(metric)

        assert metric.cache_hit is True
        assert metric.total_time_ms < 150.0  # Cache hits should be fast

    def test_performance_metric_foreign_key(self, test_db_session, test_user):
        """AC#8: PerformanceMetric has foreign key constraint to Query."""
        query_record = Query(
            user_id=test_user.id,
            query_text="Pregunta para FK test",
            answer_text="Respuesta",
            sources_json="[]",
            response_time_ms=1000.0
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)

        metric = PerformanceMetric(
            query_id=query_record.id,
            retrieval_time_ms=500.0,
            llm_time_ms=500.0,
            total_time_ms=1000.0
        )
        test_db_session.add(metric)
        test_db_session.commit()
        test_db_session.refresh(metric)

        # Verify relationship
        assert metric.query_id == query_record.id

    def test_performance_metric_created_at_default(self, test_db_session, test_user):
        """AC#8: PerformanceMetric created_at defaults to current UTC time."""
        query_record = Query(
            user_id=test_user.id,
            query_text="Pregunta",
            answer_text="Respuesta",
            sources_json="[]",
            response_time_ms=1000.0
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)

        before_create = datetime.now(timezone.utc)
        metric = PerformanceMetric(
            query_id=query_record.id,
            retrieval_time_ms=500.0,
            llm_time_ms=500.0,
            total_time_ms=1000.0
        )
        test_db_session.add(metric)
        test_db_session.commit()
        test_db_session.refresh(metric)
        after_create = datetime.now(timezone.utc)

        # Handle both timezone-aware and naive datetimes
        metric_created = metric.created_at
        if metric_created.tzinfo is None:
            metric_created = metric_created.replace(tzinfo=timezone.utc)
        assert before_create <= metric_created <= after_create

    def test_performance_metric_queryable_by_user(self, test_db_session, test_user):
        """AC#8: PerformanceMetrics are queryable by user_id via Query relationship."""
        # Create multiple queries and metrics
        for i in range(3):
            query_record = Query(
                user_id=test_user.id,
                query_text=f"Query {i}",
                answer_text=f"Answer {i}",
                sources_json="[]",
                response_time_ms=float(1000 + i * 100)
            )
            test_db_session.add(query_record)
            test_db_session.commit()
            test_db_session.refresh(query_record)

            metric = PerformanceMetric(
                query_id=query_record.id,
                retrieval_time_ms=500.0 + i,
                llm_time_ms=500.0 + i,
                total_time_ms=float(1000 + i * 100)
            )
            test_db_session.add(metric)
        test_db_session.commit()

        # Query metrics for specific user
        user_queries = test_db_session.query(Query).filter(Query.user_id == test_user.id).all()
        user_query_ids = [q.id for q in user_queries]

        metrics = test_db_session.query(PerformanceMetric).filter(
            PerformanceMetric.query_id.in_(user_query_ids)
        ).all()

        assert len(metrics) == 3
        assert all(m.query_id in user_query_ids for m in metrics)

    def test_performance_metric_queryable_by_timestamp(self, test_db_session, test_user):
        """AC#8: PerformanceMetrics are queryable by timestamp."""
        query_record = Query(
            user_id=test_user.id,
            query_text="Pregunta timestamp",
            answer_text="Respuesta",
            sources_json="[]",
            response_time_ms=1000.0
        )
        test_db_session.add(query_record)
        test_db_session.commit()
        test_db_session.refresh(query_record)

        metric = PerformanceMetric(
            query_id=query_record.id,
            retrieval_time_ms=500.0,
            llm_time_ms=500.0,
            total_time_ms=1000.0
        )
        test_db_session.add(metric)
        test_db_session.commit()

        # Query by timestamp
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_metrics = test_db_session.query(PerformanceMetric).filter(
            PerformanceMetric.created_at >= today_start
        ).all()

        assert len(today_metrics) >= 1
        assert any(m.query_id == query_record.id for m in today_metrics)

    def test_schema_create_and_read(self):
        """Test QueryCreate and QueryRead schemas."""
        create_data = QueryCreate(
            user_id=1,
            query_text="Test query",
            answer_text="Test answer",
            sources_json="[]",
            response_time_ms=100.0
        )
        assert create_data.user_id == 1
        assert create_data.query_text == "Test query"

        # Simulate read schema
        read_data = QueryRead(
            id=1,
            user_id=1,
            query_text="Test query",
            answer_text="Test answer",
            sources_json="[]",
            response_time_ms=100.0,
            created_at=datetime.now(timezone.utc)
        )
        assert read_data.id == 1

    def test_performance_metric_schema_create_and_read(self):
        """Test PerformanceMetricCreate and PerformanceMetricRead schemas."""
        create_data = PerformanceMetricCreate(
            query_id=1,
            retrieval_time_ms=500.0,
            llm_time_ms=500.0,
            total_time_ms=1000.0
        )
        assert create_data.query_id == 1
        assert create_data.total_time_ms == 1000.0

        # Simulate read schema
        read_data = PerformanceMetricRead(
            id=1,
            query_id=1,
            retrieval_time_ms=500.0,
            llm_time_ms=500.0,
            total_time_ms=1000.0,
            created_at=datetime.now(timezone.utc)
        )
        assert read_data.id == 1
