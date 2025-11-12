#!/usr/bin/env python3
"""
Script de inicio del servidor de desarrollo para el Asistente de Conocimiento API.

Este script:
1. Carga las variables de entorno desde .env usando python-dotenv
2. Valida la configuración usando el sistema de Pydantic Settings
3. Inicializa y ejecuta el servidor FastAPI con uvicorn en modo desarrollo

Uso:
    poetry run python run.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al PYTHONPATH para importaciones absolutas
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def main():
    """Punto de entrada principal del servidor de desarrollo."""

    print("=" * 80)
    print("🚀 INICIANDO ASISTENTE DE CONOCIMIENTO - SERVIDOR DE DESARROLLO")
    print("=" * 80)

    # 1. Cargar variables de entorno explícitamente desde .env
    from dotenv import load_dotenv

    env_path = current_dir / ".env"
    if not env_path.exists():
        print("⚠️  ADVERTENCIA: No se encontró archivo .env")
        print(f"   Ubicación esperada: {env_path}")
        print("   Copia .env.example a .env y configura las variables necesarias")
        print("   Comando: cp .env.example .env")
        sys.exit(1)

    # Cargar .env explícitamente
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Variables de entorno cargadas desde: {env_path}")

    # 2. Validar configuración usando get_settings()
    try:
        from app.core.config import get_settings
        settings = get_settings()

        print("\n📋 CONFIGURACIÓN VALIDADA:")
        print(f"   • Entorno: {settings.fastapi_env}")
        print(f"   • Debug: {settings.debug}")
        print(f"   • Base de datos: {settings.database_url}")
        print(f"   • Puerto: 8000")
        print(f"   • Host: 0.0.0.0")
        print(f"   • Modo: Desarrollo (auto-reload activado)")

        # Validar que SECRET_KEY esté configurado correctamente
        if len(settings.secret_key) < 32:
            print("\n❌ ERROR: SECRET_KEY debe tener al menos 32 caracteres")
            print("   Genera una clave segura con:")
            print('   python -c "import secrets; print(secrets.token_hex(32))"')
            sys.exit(1)

        print(f"   • SECRET_KEY: {'*' * 16} (configurado correctamente)")

    except Exception as e:
        print("\n❌ ERROR AL VALIDAR CONFIGURACIÓN:")
        print(f"   {str(e)}")
        print("\nVerifica que todas las variables requeridas estén en .env:")
        print("   • SECRET_KEY (mínimo 32 caracteres)")
        print("   • DATABASE_URL")
        print("\nConsulta .env.example para ver todas las variables disponibles")
        sys.exit(1)

    # 3. Ejecutar servidor con uvicorn
    print("\n🌐 SERVIDOR DISPONIBLE EN:")
    print("   • API: http://localhost:8000")
    print("   • Documentación interactiva: http://localhost:8000/docs")
    print("   • Documentación alternativa: http://localhost:8000/redoc")
    print("\n💡 Presiona Ctrl+C para detener el servidor")
    print("=" * 80)
    print()

    try:
        import uvicorn

        # Ejecutar servidor en modo desarrollo con auto-reload
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR AL INICIAR SERVIDOR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
