"""
HTTPS Redirect Middleware

Fuerza HTTPS en producción con redirección automática (status 308).
Agrega header HSTS para prevenir downgrade attacks.

Story 5.3: Cifrado de datos en tránsito y en reposo
"""

import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware que redirige HTTP → HTTPS en producción.
    Agrega header HSTS para fortalecer seguridad en tránsito.

    Comportamiento:
    - En desarrollo: Permite HTTP normalmente
    - En producción: HTTP → HTTPS (status 308)
    - Siempre: Agrega HSTS header en respuestas HTTPS

    AC#1.2: Redirección automática HTTP → HTTPS (status 308)
    AC#1.3: HSTS header habilitado
    """

    def __init__(self, app, environment: str = "development", https_enabled: bool = True):
        """
        Args:
            app: Aplicación FastAPI
            environment: 'development' o 'production'
            https_enabled: Si False, desactiva redirección (útil para testing)
        """
        super().__init__(app)
        self.environment = environment.lower()
        self.https_enabled = https_enabled

    async def dispatch(self, request: Request, call_next):
        """
        Procesa cada request.

        En producción:
        - Si scheme == 'http' → redirecciona a 'https://host/path' (308)

        En todas las respuestas HTTPS:
        - Agrega header: Strict-Transport-Security
        """
        # Validar si es HTTP en producción
        if (
            self.environment == "production"
            and self.https_enabled
            and request.url.scheme == "http"
        ):
            # Construir URL HTTPS
            https_url = request.url.replace(scheme="https")

            logger.info(
                json.dumps({
                    "event": "https_redirect",
                    "client_ip": request.client.host if request.client else "unknown",
                    "method": request.method,
                    "path": request.url.path,
                    "from": "http",
                    "to": "https",
                    "status_code": 308
                })
            )

            # Retornar redirección con status 308 (Permanent Redirect)
            return RedirectResponse(
                url=https_url,
                status_code=308  # 308 Permanent Redirect (mantiene método HTTP)
            )

        # Procesar request normalmente
        response = await call_next(request)

        # Agregar HSTS header en respuestas HTTPS
        # max-age: 1 año (31536000 segundos)
        # includeSubDomains: aplica a todos los subdominios
        if request.url.scheme == "https" or (
            self.environment == "production" and self.https_enabled
        ):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

            logger.debug(
                json.dumps({
                    "event": "hsts_header_added",
                    "path": request.url.path,
                    "max_age_seconds": 31536000
                })
            )

        return response
