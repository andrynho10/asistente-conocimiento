import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación usando Pydantic BaseSettings.
    Carga variables desde archivo .env y las valida.
    """

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True
    )

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./database/asistente_conocimiento.db",
        description="URL de conexión a la base de datos"
    )

    # Security Configuration - CRITICAL VARIABLES
    secret_key: str = Field(
        description="Clave secreta para JWT - REQUIRED, mínimo 32 caracteres"
    )
    jwt_algorithm: str = Field(default="HS256", description="Algoritmo JWT")
    jwt_expiration_hours: int = Field(default=24, description="Horas de expiración JWT")

    # Ollama / LLM Configuration
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="URL del servidor Ollama"
    )
    ollama_model: str = Field(
        default="llama3.1:8b-instruct-q4_K_M",
        description="Modelo de lenguaje a usar en Ollama"
    )
    llm_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Temperatura para generación de texto (0.0-2.0)"
    )
    llm_max_tokens: int = Field(
        default=500,
        ge=1,
        le=8192,
        description="Máximo de tokens para respuestas LLM"
    )
    llm_context_size: int = Field(
        default=8192,
        ge=1024,
        description="Tamaño del contexto para el modelo LLM"
    )

    # Performance & Caching Configuration (Story 3.6: Task 8)
    retrieval_timeout_ms: int = Field(
        default=500,
        ge=100,
        le=10000,
        description="Timeout para búsqueda de documentos (ms). Si se excede, retorna resultados parciales."
    )
    llm_inference_timeout_s: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Timeout para inferencia LLM (segundos). Si se excede, lanza excepción."
    )
    response_cache_ttl_seconds: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="TTL para caché de respuestas (5 minutos por defecto, AC#2)"
    )
    retrieval_cache_ttl_seconds: int = Field(
        default=600,
        ge=60,
        le=3600,
        description="TTL para caché de búsqueda de documentos (10 minutos por defecto, AC#3)"
    )
    max_cache_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Tamaño máximo de caché (entradas LRU, AC#2)"
    )
    max_context_tokens: int = Field(
        default=2000,
        ge=500,
        le=8000,
        description="Máximo de tokens en contexto augmentado (AC#5 context pruning)"
    )

    # Development Settings
    fastapi_env: str = Field(
        default="development",
        description="Entorno de ejecución (development/production)"
    )
    debug: bool = Field(default=True, description="Modo debug")
    log_level: str = Field(
        default="info",
        description="Nivel de logging (debug/info/warning/error)"
    )

    # CORS Settings
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Orígenes permitidos para CORS (separados por comas)"
    )

    # Validators
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        """Validador crítico para SECRET_KEY"""
        if not v:
            raise ValueError('SECRET_KEY es requerido y no puede estar vacío')

        if len(v) < 32:
            raise ValueError(
                f'SECRET_KEY debe tener al menos 32 caracteres. Actual: {len(v)} caracteres. '
                'Genera una clave segura con: python -c "import secrets; print(secrets.token_hex(32))"'
            )

        # Verificar que no sea el valor por defecto inseguro (solo valores completos, no subcadenas)
        insecure_defaults = [
            "your-super-secret-jwt-key-change-in-production",
            "your-secret-key-here-replace-with-secure-random-value-min-64-chars",
            "secret", "test", "dev", "key"
        ]

        if v.lower() in insecure_defaults:
            raise ValueError(
                'SECRET_KEY parece ser un valor inseguro. '
                'Genera una clave segura con: python -c "import secrets; print(secrets.token_hex(32))"'
            )

        return v

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        """Validador para URL de base de datos"""
        if not v:
            raise ValueError('DATABASE_URL es requerido')

        # Validar formatos soportados
        supported_schemes = ['sqlite', 'postgresql', 'mysql']
        scheme = v.split('://')[0] if '://' in v else None

        if not scheme or scheme not in supported_schemes:
            raise ValueError(
                f'DATABASE_URL debe usar un esquema soportado: {", ".join(supported_schemes)}. '
                f'Valor actual: {v[:50]}...'
            )

        return v

    @field_validator('ollama_host')
    @classmethod
    def validate_ollama_host(cls, v):
        """Validador para URL de Ollama"""
        if not v:
            raise ValueError('OLLAMA_HOST es requerido')

        # Validar formato de URL
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError(
                f'OLLAMA_HOST debe ser una URL válida. Formato esperado: http://host:port. '
                f'Valor actual: {v}'
            )

        return v

    @field_validator('fastapi_env')
    @classmethod
    def validate_environment(cls, v):
        """Validador para entorno de ejecución"""
        valid_envs = ['development', 'testing', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(
                f'FASTAPI_ENV debe ser uno de: {", ".join(valid_envs)}. Valor actual: {v}'
            )
        return v.lower()

    def validate_all_settings(self) -> None:
        """
        Método de validación completo que se ejecuta al inicio.
        Lanza ValueError si alguna validación crítica falla.
        """
        try:
            # Forzar validación de todos los campos
            _ = self.secret_key
            _ = self.database_url
            _ = self.ollama_host
            _ = self.fastapi_env

        except ValueError as e:
            raise ValueError(f"❌ Error de configuración: {e}")

    @classmethod
    def create_with_validation(cls) -> 'Settings':
        """
        Factory method que crea instancia y ejecuta validación completa.
        Uso en startup de la aplicación.
        """
        settings = cls()
        settings.validate_all_settings()
        return settings


# Singleton instance para uso en la aplicación (carga lazy)
settings = None

def get_settings() -> Settings:
    """
    Obtiene instancia singleton de Settings.
    Crea la instancia solo en la primera llamada.
    """
    global settings
    if settings is None:
        settings = Settings.create_with_validation()
    return settings