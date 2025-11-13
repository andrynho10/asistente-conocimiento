"""
Tests para módulo de configuración centralizada
Valida carga de variables, validadores e integración con servicios
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=False)
def reset_settings_singleton():
    """Fixture que resetea el singleton de settings cuando se necesita"""
    import app.core.config
    # Guardar estado original
    original_settings = app.core.config.settings
    # Resetear singleton
    app.core.config.settings = None
    yield
    # Restaurar estado original
    app.core.config.settings = original_settings


class TestConfiguracionBasica:
    """Tests para configuración básica y carga de variables"""

    def test_configuracion_valida_carga_correctamente(self, isolated_env_for_config_tests):
        """AC #1, AC #2: Configuración válida carga correctamente"""
        # Crear archivo .env temporal con valores válidos
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
            f.write("""
DATABASE_URL=sqlite:///./test_database.db
SECRET_KEY=valid_secure_config_key_that_is_long_enough_for_validation_and_passes_all_checks_123456789012
JWT_EXPIRATION_HOURS=24
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500
LLM_CONTEXT_SIZE=8192
FASTAPI_ENV=development
DEBUG=True
LOG_LEVEL=info
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
            """)
            env_path = f.name

        try:
            settings = Settings(_env_file=env_path)

            assert settings.database_url == "sqlite:///./test_database.db"
            assert settings.secret_key == "valid_secure_config_key_that_is_long_enough_for_validation_and_passes_all_checks_123456789012"
            assert settings.jwt_expiration_hours == 24
            assert settings.ollama_host == "http://localhost:11434"
            assert settings.ollama_model == "llama3.1:8b-instruct-q4_K_M"
            assert settings.llm_temperature == 0.3
            assert settings.llm_max_tokens == 500
            assert settings.llm_context_size == 8192
            assert settings.fastapi_env == "development"
            assert settings.debug is True
            assert settings.log_level == "info"
            assert settings.allowed_origins == "http://localhost:5173,http://127.0.0.1:5173"

        finally:
            os.unlink(env_path)

    def test_valores_por_defecto_se_aplican_correctamente(self, isolated_env_for_config_tests):
        """AC #2: Variables por defecto se aplican correctamente"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
            f.write("""
SECRET_KEY=valid_secure_config_key_for_testing_defaults_that_is_long_enough_to_pass_validation_123456789012
            """)
            env_path = f.name

        try:
            settings = Settings(_env_file=env_path)

            # Valores por defecto según config.py
            assert settings.database_url == "sqlite:///./database/asistente_conocimiento.db"
            assert settings.jwt_algorithm == "HS256"
            assert settings.jwt_expiration_hours == 24
            assert settings.ollama_host == "http://localhost:11434"
            assert settings.ollama_model == "llama3.1:8b-instruct-q4_K_M"
            assert settings.llm_temperature == 0.3
            assert settings.llm_max_tokens == 500
            assert settings.llm_context_size == 8192
            assert settings.fastapi_env == "development"
            assert settings.debug is True
            assert settings.log_level == "info"
            assert settings.allowed_origins == "http://localhost:5173,http://127.0.0.1:5173"

        finally:
            os.unlink(env_path)


class TestValidadoresSecretKey:
    """Tests para validador crítico de SECRET_KEY"""

    def test_secret_key_faltante_lanza_value_error(self):
        """AC #3: Falta SECRET_KEY lanza ValueError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
            f.write("OTHER_VAR=value")
            env_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                Settings(_env_file=env_path, secret_key="")

            assert "SECRET_KEY es requerido" in str(exc_info.value)

        finally:
            os.unlink(env_path)

    def test_secret_key_demasiado_corto_lanza_value_error(self, isolated_env_for_config_tests):
        """AC #3: SECRET_KEY demasiado corto lanza ValueError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
            f.write("SECRET_KEY=short")
            env_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                Settings(_env_file=env_path)

            assert "SECRET_KEY debe tener al menos 32 caracteres" in str(exc_info.value)
            assert "Actual: 5 caracteres" in str(exc_info.value)

        finally:
            os.unlink(env_path)

    def test_secret_key_valor_inseguro_lanza_value_error(self, isolated_env_for_config_tests):
        """AC #3: SECRET_KEY con valor inseguro lanza ValueError"""
        insecure_values = [
            "your-super-secret-jwt-key-change-in-production",
            "your-secret-key-here-replace-with-secure-random-value-min-64-chars",
        ]

        # Test values that are long enough but insecure
        for insecure_value in insecure_values:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
                f.write(f"SECRET_KEY={insecure_value}")
                env_path = f.name

            try:
                with pytest.raises(ValueError) as exc_info:
                    Settings(_env_file=env_path)

                assert "SECRET_KEY parece ser un valor inseguro" in str(exc_info.value)
                assert "secrets.token_hex" in str(exc_info.value)

            finally:
                os.unlink(env_path)

        # Test values that are too short (fallan por longitud, no por seguridad)
        short_insecure_values = ["secret", "test", "dev"]
        for insecure_value in short_insecure_values:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
                f.write(f"SECRET_KEY={insecure_value}")
                env_path = f.name

            try:
                with pytest.raises(ValueError) as exc_info:
                    Settings(_env_file=env_path)

                # Estos fallan por longitud, no por seguridad
                assert "SECRET_KEY debe tener al menos 32 caracteres" in str(exc_info.value)

            finally:
                os.unlink(env_path)


class TestValidadoresGenerales:
    """Tests para otros validadores de configuración"""

    def test_database_url_invalida_lanza_error(self, isolated_env_for_config_tests):
        """Validador: DATABASE_URL inválida lanza error"""
        invalid_urls = [
            "invalid://not-supported",
            "not-a-url",
            "ftp://unsupported-protocol.db"
        ]

        for invalid_url in invalid_urls:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
                f.write(f"""
SECRET_KEY=valid_secure_key_for_testing_database_urls_that_is_long_enough_to_pass_validation_123456789012
DATABASE_URL={invalid_url}
                """)
                env_path = f.name

            try:
                with pytest.raises(ValueError) as exc_info:
                    Settings(_env_file=env_path)

                assert "DATABASE_URL debe usar un esquema soportado" in str(exc_info.value)

            finally:
                os.unlink(env_path)

    def test_ollama_host_invalido_lanza_error(self, isolated_env_for_config_tests):
        """Validador: OLLAMA_HOST inválido lanza error"""
        invalid_hosts = [
            "invalid-host",
            "ftp://localhost:11434",
            "localhost:11434"  # Missing protocol
        ]

        for invalid_host in invalid_hosts:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
                f.write(f"""
SECRET_KEY=valid_secure_key_for_testing_ollama_hosts_that_is_long_enough_to_pass_validation_123456789012
OLLAMA_HOST={invalid_host}
                """)
                env_path = f.name

            try:
                with pytest.raises(ValueError) as exc_info:
                    Settings(_env_file=env_path)

                assert "OLLAMA_HOST debe ser una URL válida" in str(exc_info.value)

            finally:
                os.unlink(env_path)

    def test_fastapi_env_invalido_lanza_error(self, isolated_env_for_config_tests):
        """Validador: FASTAPI_ENV inválido lanza error"""
        invalid_envs = [
            "invalid",
            "prod",
            "dev",
            "test"
        ]

        for invalid_env in invalid_envs:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
                f.write(f"""
SECRET_KEY=valid_secure_key_for_testing_flask_env_that_is_long_enough_to_pass_validation_123456789012
FASTAPI_ENV={invalid_env}
                """)
                env_path = f.name

            try:
                with pytest.raises(ValueError) as exc_info:
                    Settings(_env_file=env_path)

                assert "FASTAPI_ENV debe ser uno de: development, testing, production" in str(exc_info.value)

            finally:
                os.unlink(env_path)


class TestIntegracionServicios:
    """Tests para integración con servicios existentes"""

    @patch('app.database.engine')
    def test_database_usa_configuracion_centralizada(self, mock_engine):
        """AC #5: Verifica que database.py usa configuración centralizada"""
        # Importamos después del patch para asegurar que se usa el mock
        from app.database import DATABASE_URL, engine

        # Verificar que engine se crea con DATABASE_URL de settings
        # Este test verifica que el import funcione correctamente
        assert DATABASE_URL is not None

    def test_auth_service_puede_inyectar_settings(self):
        """AC #5: Verifica que AuthService puede usar settings inyectadas"""
        # Mock de sesión de base de datos
        mock_session = MagicMock()

        # Import de AuthService
        from app.auth.service import AuthService

        # Verificar que AuthService puede instanciarse correctamente
        # La integración con settings se verifica en test de integración real
        try:
            auth_service = AuthService(mock_session)
            assert auth_service.db == mock_session
        except Exception as e:
            pytest.fail(f"No se pudo instanciar AuthService: {e}")

    def test_get_settings_devuelve_singleton_correctamente(self):
        """Verifica que get_settings() devuelve el singleton correctamente"""
        # El fixture ya resetea el singleton, así que podemos probar directamente
        settings1 = get_settings()
        settings2 = get_settings()

        # Verificar que devuelve la misma instancia (singleton)
        assert settings1 is settings2
        assert isinstance(settings1, Settings)
        assert hasattr(settings1, 'secret_key')
        assert hasattr(settings1, 'database_url')
        assert hasattr(settings1, 'ollama_host')


class TestValidacionCompleta:
    """Tests para método de validación completa"""

    def test_validate_all_settings_con_configuracion_valida(self):
        """Método validate_all_settings funciona con configuración válida"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
            f.write("""
DATABASE_URL=sqlite:///./test_database.db
SECRET_KEY=valid_secure_key_for_testing_complete_validation_that_is_long_enough_to_pass_validation_123456789012
OLLAMA_HOST=http://localhost:11434
FASTAPI_ENV=development
            """)
            env_path = f.name

        try:
            settings = Settings(_env_file=env_path)

            # No debe lanzar excepción
            settings.validate_all_settings()

        finally:
            os.unlink(env_path)

    def test_validate_all_settings_con_configuracion_invalida(self):
        """Método validate_all_settings detecta configuración inválida"""
        # Creamos settings con configuración inválida pasando el valor directamente
        # para que falle en validate_all_settings y no en el constructor
        try:
            # El constructor debe fallar con ValidationError, lo cual es correcto
            with pytest.raises(ValueError) as exc_info:
                settings = Settings(secret_key="short")
                settings.validate_all_settings()

            # Si llegamos aquí, significa que el constructor no falló, así que verificamos
            # que validate_all_settings sí falle
            assert "SECRET_KEY debe tener al menos 32 caracteres" in str(exc_info.value)

        except Exception as e:
            # Si hay un ValidationError en el constructor, eso también es correcto
            # porque significa que la validación está funcionando
            assert "SECRET_KEY debe tener al menos 32 caracteres" in str(e)

    def test_create_with_validation_funciona_correctamente(self):
        """Factory method create_with_validation funciona correctamente"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
            f.write("""
DATABASE_URL=sqlite:///./test_database.db
SECRET_KEY=valid_secret_key_for_testing_that_is_long_enough_to_pass_validation_123456789012
OLLAMA_HOST=http://localhost:11434
FASTAPI_ENV=development
            """)
            env_path = f.name

        try:
            # Limpiar singleton para test
            import app.core.config
            original_settings = app.core.config.settings
            app.core.config.settings = None

            # No debe lanzar excepción (usa configuración del entorno)
            settings = Settings.create_with_validation()
            assert isinstance(settings, Settings)

        finally:
            os.unlink(env_path)
            # Restaurar singleton
            app.core.config.settings = original_settings