"""
LLM Service - Ollama Integration for Local AI Generation

This module provides integration with Ollama API for local LLM inference,
ensuring data sovereignty and compliance with RNF2 (<2s response time).
"""

import logging
import asyncio
from typing import Optional, Dict, Any
import httpx
from ollama import Client, AsyncClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaLLMService:
    """
    Service for interacting with Ollama API for local LLM inference.

    Provides health checking and text generation capabilities with
    proper error handling and timeout management.
    """

    def __init__(
        self,
        host: str = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        timeout: int = 10
    ):
        """
        Initialize Ollama LLM Service.

        Args:
            host: Ollama server host URL
            model: Model name to use for generation
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        self.host = host or settings.ollama_host
        self.model = model or settings.ollama_model
        self.temperature = temperature or settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.timeout = timeout

        # Initialize synchronous and asynchronous clients
        self.client = Client(host=self.host, timeout=self.timeout)
        self.async_client = AsyncClient(host=self.host, timeout=self.timeout)

        logger.info(
            f"OllamaLLMService initialized with host={self.host}, "
            f"model={self.model}, temperature={self.temperature}, "
            f"max_tokens={self.max_tokens}, timeout={self.timeout}s"
        )

    def health_check(self) -> bool:
        """
        Check if Ollama service is available and responsive.

        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            # Try to list available models
            models = self.client.list()

            # Check if our configured model is available
            available_models = [model['name'] for model in models.get('models', [])]
            model_available = self.model in available_models

            if model_available:
                logger.info(f"Ollama health check passed - model {self.model} available")
                return True
            else:
                logger.warning(
                    f"Ollama responding but model {self.model} not found. "
                    f"Available models: {available_models}"
                )
                return False

        except ConnectionError as e:
            logger.warning(f"Ollama health check failed - Connection error: {e}")
            return False
        except TimeoutError as e:
            logger.warning(f"Ollama health check failed - Timeout after {self.timeout}s: {e}")
            return False
        except Exception as e:
            logger.error(f"Ollama health check failed - Unexpected error: {e}")
            return False

    async def health_check_async(self) -> bool:
        """
        Async version of health check.

        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            models = await self.async_client.list()
            available_models = [model['name'] for model in models.get('models', [])]
            model_available = self.model in available_models

            if model_available:
                logger.info(f"Ollama async health check passed - model {self.model} available")
                return True
            else:
                logger.warning(
                    f"Ollama responding but model {self.model} not found. "
                    f"Available models: {available_models}"
                )
                return False

        except ConnectionError as e:
            logger.warning(f"Ollama async health check failed - Connection error: {e}")
            return False
        except TimeoutError as e:
            logger.warning(f"Ollama async health check failed - Timeout after {self.timeout}s: {e}")
            return False
        except Exception as e:
            logger.error(f"Ollama async health check failed - Unexpected error: {e}")
            return False

    def generate_response(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Generate a response using the configured LLM model.

        Args:
            prompt: Input prompt for generation
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Whether to stream response (not implemented yet)

        Returns:
            Generated text response

        Raises:
            ConnectionError: If Ollama is not available
            TimeoutError: If request times out
            ValueError: If prompt is empty
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Use provided values or fall back to instance defaults
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        try:
            logger.debug(f"Generating response with model {self.model}, temp={temp}, max_tokens={tokens}")

            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': temp,
                    'num_predict': tokens,
                    'top_k': 40,
                    'top_p': 0.9,
                    'repeat_penalty': 1.1
                }
            )

            generated_text = response.get('response', '')
            logger.debug(f"Generated {len(generated_text)} characters")

            return generated_text

        except ConnectionError as e:
            logger.error(f"Failed to generate response - Connection error: {e}")
            raise ConnectionError(f"Ollama service unavailable: {e}")
        except TimeoutError as e:
            logger.error(f"Failed to generate response - Timeout: {e}")
            raise TimeoutError(f"Request timed out after {self.timeout}s")
        except Exception as e:
            logger.error(f"Failed to generate response - Unexpected error: {e}")
            raise

    async def generate_response_async(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Async version of generate_response.

        Args:
            prompt: Input prompt for generation
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text response
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        try:
            logger.debug(f"Generating async response with model {self.model}, temp={temp}, max_tokens={tokens}")

            response = await self.async_client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': temp,
                    'num_predict': tokens,
                    'top_k': 40,
                    'top_p': 0.9,
                    'repeat_penalty': 1.1
                }
            )

            generated_text = response.get('response', '')
            logger.debug(f"Generated async {len(generated_text)} characters")

            return generated_text

        except ConnectionError as e:
            logger.error(f"Failed to generate async response - Connection error: {e}")
            raise ConnectionError(f"Ollama service unavailable: {e}")
        except TimeoutError as e:
            logger.error(f"Failed to generate async response - Timeout: {e}")
            raise TimeoutError(f"Request timed out after {self.timeout}s")
        except Exception as e:
            logger.error(f"Failed to generate async response - Unexpected error: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the configured model.

        Returns:
            Dictionary with model information
        """
        try:
            # Get model details
            model_info = self.client.show(self.model)

            return {
                'model': self.model,
                'available': True,
                'details': model_info,
                'host': self.host,
                'timeout': self.timeout
            }

        except Exception as e:
            logger.warning(f"Failed to get model info: {e}")
            return {
                'model': self.model,
                'available': False,
                'error': str(e),
                'host': self.host,
                'timeout': self.timeout
            }

    async def get_ollama_version(self) -> Optional[str]:
        """
        Get Ollama server version.

        Returns:
            Version string if available, None otherwise
        """
        try:
            # Use httpx directly to get version from Ollama API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.host}/api/version")
                if response.status_code == 200:
                    data = response.json()
                    return data.get('version')
        except Exception as e:
            logger.warning(f"Failed to get Ollama version: {e}")

        return None


# Global service instance (lazy initialization)
llm_service = None

def get_llm_service() -> OllamaLLMService:
    """Get global LLM service instance."""
    global llm_service
    if llm_service is None:
        llm_service = OllamaLLMService()
    return llm_service