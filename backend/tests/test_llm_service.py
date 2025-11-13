"""
Tests for LLM Service - Ollama Integration

Unit tests for the OllamaLLMService class, covering health checks,
text generation, error handling, and timeout scenarios.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import httpx
from ollama import Client

from app.services.llm_service import OllamaLLMService
from app.core.config import Settings


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Settings(
        ollama_host="http://localhost:11434",
        ollama_model="llama3.1:8b-instruct-q4_K_M",
        llm_temperature=0.3,
        llm_max_tokens=500,
        llm_context_size=8192
    )

@pytest.fixture
def llm_service(mock_settings):
    """Create LLM service instance for testing."""
    with patch('app.services.llm_service.settings', mock_settings):
        return OllamaLLMService()

@pytest.fixture
def mock_client():
    """Mock Ollama client."""
    return Mock(spec=Client)

@pytest.fixture
def mock_async_client():
    """Mock async Ollama client."""
    return AsyncMock()

@pytest.fixture
def llm_service_with_mocks(mock_settings, mock_client, mock_async_client):
    """Create LLM service with mocked clients."""
    with patch('app.services.llm_service.settings', mock_settings), \
         patch('app.services.llm_service.Client') as mock_client_class, \
         patch('app.services.llm_service.AsyncClient') as mock_async_client_class:

        mock_client_class.return_value = mock_client
        mock_async_client_class.return_value = mock_async_client

        service = OllamaLLMService()
        service.client = mock_client
        service.async_client = mock_async_client
        return service


class TestOllamaLLMService:
    """Test cases for OllamaLLMService."""


class TestOllamaLLMServiceInit:
    """Test LLM service initialization."""

    def test_init_with_default_settings(self):
        """Test service initialization with default settings."""
        with patch('app.services.llm_service.settings') as mock_settings:
            mock_settings.ollama_host = "http://localhost:11434"
            mock_settings.ollama_model = "llama3.1:8b"
            mock_settings.llm_temperature = 0.3
            mock_settings.llm_max_tokens = 500

            with patch('app.services.llm_service.Client'), \
                 patch('app.services.llm_service.AsyncClient'):

                service = OllamaLLMService()

                assert service.host == "http://localhost:11434"
                assert service.model == "llama3.1:8b"
                assert service.temperature == 0.3
                assert service.max_tokens == 500
                assert service.timeout == 10

    def test_init_with_custom_parameters(self):
        """Test service initialization with custom parameters."""
        with patch('app.services.llm_service.Client'), \
             patch('app.services.llm_service.AsyncClient'):

            service = OllamaLLMService(
                host="http://custom:11434",
                model="custom-model",
                temperature=0.7,
                max_tokens=1000,
                timeout=20
            )

            assert service.host == "http://custom:11434"
            assert service.model == "custom-model"
            assert service.temperature == 0.7
            assert service.max_tokens == 1000
            assert service.timeout == 20


class TestHealthCheck:
    """Test health check functionality."""

    def test_health_check_success(self, llm_service_with_mocks):
        """Test successful health check."""
        service = llm_service_with_mocks

        # Mock successful response
        service.client.list.return_value = {
            'models': [
                {'name': 'llama3.1:8b-instruct-q4_K_M'},
                {'name': 'other-model'}
            ]
        }

        result = service.health_check()

        assert result is True
        service.client.list.assert_called_once()

    def test_health_check_model_not_available(self, llm_service_with_mocks):
        """Test health check when configured model is not available."""
        service = llm_service_with_mocks

        # Mock response with different models
        service.client.list.return_value = {
            'models': [
                {'name': 'other-model'},
                {'name': 'another-model'}
            ]
        }

        result = service.health_check()

        assert result is False
        service.client.list.assert_called_once()

    def test_health_check_connection_error(self, llm_service_with_mocks):
        """Test health check with connection error."""
        service = llm_service_with_mocks

        # Mock connection error
        service.client.list.side_effect = ConnectionError("Connection refused")

        result = service.health_check()

        assert result is False
        service.client.list.assert_called_once()

    def test_health_check_timeout_error(self, llm_service_with_mocks):
        """Test health check with timeout error."""
        service = llm_service_with_mocks

        # Mock timeout error
        service.client.list.side_effect = TimeoutError("Request timeout")

        result = service.health_check()

        assert result is False
        service.client.list.assert_called_once()

    def test_health_check_unexpected_error(self, llm_service_with_mocks):
        """Test health check with unexpected error."""
        service = llm_service_with_mocks

        # Mock unexpected error
        service.client.list.side_effect = Exception("Unexpected error")

        result = service.health_check()

        assert result is False
        service.client.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_async_success(self, llm_service_with_mocks):
        """Test successful async health check."""
        service = llm_service_with_mocks

        service.async_client.list.return_value = {
            'models': [
                {'name': 'llama3.1:8b-instruct-q4_K_M'}
            ]
        }

        result = await service.health_check_async()

        assert result is True
        service.async_client.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_async_failure(self, llm_service_with_mocks):
        """Test async health check failure."""
        service = llm_service_with_mocks

        service.async_client.list.side_effect = ConnectionError("Connection failed")

        result = await service.health_check_async()

        assert result is False
        service.async_client.list.assert_called_once()


class TestGenerateResponse:
    """Test text generation functionality."""

    def test_generate_response_success(self, llm_service_with_mocks):
        """Test successful text generation."""
        service = llm_service_with_mocks

        # Mock successful generation
        service.client.generate.return_value = {
            'response': 'Generated text response'
        }

        result = service.generate_response('Test prompt')

        assert result == 'Generated text response'
        service.client.generate.assert_called_once()

    def test_generate_response_with_custom_parameters(self, llm_service_with_mocks):
        """Test text generation with custom parameters."""
        service = llm_service_with_mocks

        service.client.generate.return_value = {
            'response': 'Custom response'
        }

        result = service.generate_response(
            prompt='Test prompt',
            temperature=0.7,
            max_tokens=1000
        )

        assert result == 'Custom response'

        # Verify call arguments
        call_args = service.client.generate.call_args
        assert call_args[1]['prompt'] == 'Test prompt'
        assert call_args[1]['options']['temperature'] == 0.7
        assert call_args[1]['options']['num_predict'] == 1000

    def test_generate_response_empty_prompt(self, llm_service_with_mocks):
        """Test text generation with empty prompt."""
        service = llm_service_with_mocks

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            service.generate_response('')

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            service.generate_response('   ')

    def test_generate_response_whitespace_prompt(self, llm_service_with_mocks):
        """Test text generation with whitespace-only prompt."""
        service = llm_service_with_mocks

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            service.generate_response('   \t\n   ')

    def test_generate_response_connection_error(self, llm_service_with_mocks):
        """Test text generation with connection error."""
        service = llm_service_with_mocks

        service.client.generate.side_effect = ConnectionError("Connection failed")

        with pytest.raises(ConnectionError, match="Ollama service unavailable"):
            service.generate_response("Test prompt")

    def test_generate_response_timeout_error(self, llm_service_with_mocks):
        """Test text generation with timeout error."""
        service = llm_service_with_mocks

        service.client.generate.side_effect = TimeoutError("Request timeout")

        with pytest.raises(TimeoutError, match="Request timed out"):
            service.generate_response("Test prompt")

    def test_generate_response_unexpected_error(self, llm_service_with_mocks):
        """Test text generation with unexpected error."""
        service = llm_service_with_mocks

        service.client.generate.side_effect = Exception("Unexpected error")

        with pytest.raises(Exception, match="Unexpected error"):
            service.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_async_success(self, llm_service_with_mocks):
        """Test successful async text generation."""
        service = llm_service_with_mocks

        service.async_client.generate.return_value = {
            'response': 'Async generated response'
        }

        result = await service.generate_response_async('Test prompt')

        assert result == 'Async generated response'
        service.async_client.generate.assert_called_once()


class TestGetModelInfo:
    """Test model information retrieval."""

    def test_get_model_info_success(self, llm_service_with_mocks):
        """Test successful model info retrieval."""
        service = llm_service_with_mocks

        mock_model_info = {
            'model': 'llama3.1:8b-instruct-q4_K_M',
            'details': {'size': 5033164800, 'format': 'gguf'}
        }
        service.client.show.return_value = mock_model_info

        result = service.get_model_info()

        assert result['model'] == service.model
        assert result['available'] is True
        assert result['details'] == mock_model_info
        assert result['host'] == service.host
        assert result['timeout'] == service.timeout

    def test_get_model_info_failure(self, llm_service_with_mocks):
        """Test model info retrieval failure."""
        service = llm_service_with_mocks

        service.client.show.side_effect = Exception("Model not found")

        result = service.get_model_info()

        assert result['model'] == service.model
        assert result['available'] is False
        assert 'error' in result
        assert result['host'] == service.host
        assert result['timeout'] == service.timeout


class TestGetOllamaVersion:
    """Test Ollama version retrieval."""

    @pytest.mark.asyncio
    async def test_get_ollama_version_success(self, llm_service_with_mocks):
        """Test successful Ollama version retrieval."""
        service = llm_service_with_mocks

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'version': '0.1.20'}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            version = await service.get_ollama_version()

            assert version == '0.1.20'

    @pytest.mark.asyncio
    async def test_get_ollama_version_failure(self, llm_service_with_mocks):
        """Test Ollama version retrieval failure."""
        service = llm_service_with_mocks

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client

            version = await service.get_ollama_version()

            assert version is None


class TestErrorHandling:
    """Test comprehensive error handling."""

    def test_graceful_degradation_on_service_unavailable(self, llm_service_with_mocks):
        """Test graceful degradation when service is unavailable."""
        service = llm_service_with_mocks

        # Mock all operations to fail
        service.client.list.side_effect = ConnectionError("Service unavailable")
        service.client.generate.side_effect = ConnectionError("Service unavailable")
        service.client.show.side_effect = ConnectionError("Service unavailable")

        # Health check should return False, not raise exception
        health = service.health_check()
        assert health is False

        # Generation should raise appropriate exception
        with pytest.raises(ConnectionError):
            service.generate_response("Test prompt")

        # Model info should return unavailable status
        info = service.get_model_info()
        assert info['available'] is False


class TestLogging:
    """Test logging functionality."""

    def test_logging_on_operations(self, llm_service_with_mocks, caplog):
        """Test that operations are properly logged."""
        import logging

        service = llm_service_with_mocks

        # Set up logging capture
        caplog.set_level(logging.INFO)

        # Test successful health check
        service.client.list.return_value = {
            'models': [{'name': 'llama3.1:8b-instruct-q4_K_M'}]
        }

        service.health_check()

        # Check that success was logged
        assert "health check passed" in caplog.text.lower()

        # Test failed health check
        service.client.list.side_effect = ConnectionError("Connection failed")

        service.health_check()

        # Check that failure was logged
        assert "health check failed" in caplog.text.lower()


class TestHealthCheckEdgeCases:
    """Test edge cases for health check not covered in main tests."""

    def test_health_check_model_not_available_logging(self, llm_service_with_mocks, caplog):
        """Test health check when model not found (covers lines 111-115)."""
        service = llm_service_with_mocks

        # Mock response with different models but include the specific warning lines
        service.client.list.return_value = {
            'models': [
                {'name': 'other-model'},
                {'name': 'another-model'}
            ]
        }

        import logging
        caplog.set_level(logging.WARNING)

        result = service.health_check()

        assert result is False
        service.client.list.assert_called_once()

        # Check that specific warning was logged
        assert "model llama3.1:8b-instruct-q4_k_m not found" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_health_check_async_model_not_available_logging(self, llm_service_with_mocks, caplog):
        """Test async health check when model not found (covers lines 111-115 async)."""
        service = llm_service_with_mocks

        service.async_client.list.return_value = {
            'models': [
                {'name': 'other-model'},
                {'name': 'another-model'}
            ]
        }

        import logging
        caplog.set_level(logging.WARNING)

        result = await service.health_check_async()

        assert result is False
        service.async_client.list.assert_called_once()

        # Check that specific warning was logged
        assert "model llama3.1:8b-instruct-q4_k_m not found" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_health_check_async_timeout_error(self, llm_service_with_mocks, caplog):
        """Test async health check with timeout error (covers lines 120-125)."""
        service = llm_service_with_mocks

        # Mock timeout error
        service.async_client.list.side_effect = TimeoutError("Request timeout after 10s")

        import logging
        caplog.set_level(logging.WARNING)

        result = await service.health_check_async()

        assert result is False
        service.async_client.list.assert_called_once()

        # Check that specific timeout warning was logged
        assert "timeout after 10s" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_health_check_async_unexpected_error(self, llm_service_with_mocks, caplog):
        """Test async health check with unexpected error (covers lines 123-125)."""
        service = llm_service_with_mocks

        # Mock unexpected error
        service.async_client.list.side_effect = RuntimeError("Unexpected runtime error")

        import logging
        caplog.set_level(logging.ERROR)

        result = await service.health_check_async()

        assert result is False
        service.async_client.list.assert_called_once()

        # Check that unexpected error was logged
        assert "unexpected error" in caplog.text.lower()


class TestGenerateResponseEdgeCases:
    """Test edge cases for generate_response not covered in main tests."""

    @pytest.mark.asyncio
    async def test_generate_response_async_timeout_error(self, llm_service_with_mocks):
        """Test async text generation with timeout error (covers lines 234-236)."""
        service = llm_service_with_mocks

        service.async_client.generate.side_effect = TimeoutError("Request timeout")

        with pytest.raises(TimeoutError, match="Request timed out after 10s"):
            await service.generate_response_async("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_async_connection_error(self, llm_service_with_mocks):
        """Test async text generation with connection error (covers lines 231-233)."""
        service = llm_service_with_mocks

        service.async_client.generate.side_effect = ConnectionError("Connection failed")

        with pytest.raises(ConnectionError, match="Ollama service unavailable"):
            await service.generate_response_async("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_async_unexpected_error(self, llm_service_with_mocks):
        """Test async text generation with unexpected error (covers lines 237-239)."""
        service = llm_service_with_mocks

        service.async_client.generate.side_effect = RuntimeError("Unexpected runtime error")

        with pytest.raises(RuntimeError, match="Unexpected runtime error"):
            await service.generate_response_async("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_async_with_parameters(self, llm_service_with_mocks):
        """Test async text generation with custom parameters (covers missing async test)."""
        service = llm_service_with_mocks

        service.async_client.generate.return_value = {
            'response': 'Async custom response'
        }

        result = await service.generate_response_async(
            prompt='Test prompt',
            temperature=0.8,
            max_tokens=750
        )

        assert result == 'Async custom response'

        # Verify call arguments for async version
        call_args = service.async_client.generate.call_args
        assert call_args[1]['prompt'] == 'Test prompt'
        assert call_args[1]['options']['temperature'] == 0.8
        assert call_args[1]['options']['num_predict'] == 750


class TestIntegration:
    """Integration tests for LLM service."""

    def test_real_ollama_connection(self):
        """
        Test real connection to Ollama (integration test).

        This test requires Ollama to be running and is marked as slow.
        It should only run in environments where Ollama is available.
        """
        pytest.skip("Integration test - requires Ollama to be running")

        # This would be the actual test if Ollama is available
        service = OllamaLLMService(timeout=5)

        if service.health_check():
            # If service is available, test generation
            result = service.generate_response("Hello", max_tokens=10)
            assert len(result) > 0
        else:
            # If service is not available, that's also valid
            pytest.skip("Ollama not available for integration test")


@pytest.fixture
def sample_llm_responses():
    """Sample LLM responses for testing."""
    return {
        'health_success': {
            'models': [
                {'name': 'llama3.1:8b-instruct-q4_K_M'},
                {'name': 'other-model'}
            ]
        },
        'generation_success': {
            'response': 'This is a generated response.',
            'model': 'llama3.1:8b-instruct-q4_K_M',
            'created_at': '2025-11-13T10:30:00Z',
            'done': True
        },
        'model_info': {
            'model': 'llama3.1:8b-instruct-q4_K_M',
            'details': {
                'format': 'gguf',
                'family': 'llama',
                'families': None,
                'parameter_size': '8B',
                'quantization_level': 'q4_K_M'
            },
            'modified_at': '2025-11-13T10:30:00Z',
            'size': 5033164800
        }
    }