from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.auth.routes import router as auth_router
from app.routes.knowledge import router as knowledge_router
from app.routes.ia import router as ia_router
from app.auth.models import HealthResponse
from app.core.config import get_settings
from app.services.llm_service import get_llm_service
from app.exceptions import (
    IAServiceException,
    QueryValidationError,
    OllamaUnavailableError,
    RateLimitError,
    LLMGenerationError,
    DatabaseError,
    RetrievalServiceError
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Validar configuración y crear base de datos
    settings = get_settings()
    print(f"Iniciando Asistente de Conocimiento API en modo: {settings.fastapi_env}")
    print(f"Base de datos: {settings.database_url}")
    print(f"Servidor Ollama: {settings.ollama_host}")

    # Validación completa de la configuración ya se ejecuta al importar settings
    # pero podemos agregar mensajes específicos aquí
    create_db_and_tables()
    print("Base de datos inicializada correctamente")

    # Validar Ollama (no bloqueante)
    try:
        llm_svc = get_llm_service()
        ollama_available = await llm_svc.health_check_async()
        if ollama_available:
            print(f"Ollama service disponible - Modelo: {llm_svc.model}")
        else:
            print("Ollama service no disponible - Las funciones de IA estarán deshabilitadas")
    except Exception as e:
        print(f"Error verificando Ollama: {e} - Las funciones de IA podrían no estar disponibles")

    yield

    # Shutdown (if needed)
    print("Aplicación detenida")


app = FastAPI(
    title="Asistente de Conocimiento API",
    description="API para el Sistema de IA Generativa para Capacitación Corporativa",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configurado desde settings (obtenemos settings después de la configuración)
settings = get_settings()
allowed_origins_list = [origin.strip() for origin in settings.allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(ia_router)


# Exception handlers for IA service (Task 11: Error Handling)
@app.exception_handler(QueryValidationError)
async def query_validation_error_handler(request: Request, exc: QueryValidationError):
    """
    AC#10: Malformed requests return clear error messages.
    AC#2: Returns 400 for invalid query.
    """
    logger.warning(f"Query validation error: {exc.message}")
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": "Invalid request",
            "detail": exc.detail,
            "code": exc.error_code
        }
    )


@app.exception_handler(OllamaUnavailableError)
async def ollama_unavailable_handler(request: Request, exc: OllamaUnavailableError):
    """
    AC#10: Service gracefully handles Ollama unavailability.
    AC#1: Returns 503 when Ollama unavailable.
    """
    logger.error(f"Ollama service unavailable: {exc.message}")
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": "Service unavailable",
            "detail": exc.detail,
            "code": exc.error_code
        }
    )


@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(request: Request, exc: RateLimitError):
    """
    AC#6: Rate limiting returns 429 with error message.
    """
    logger.warning(f"Rate limit exceeded: {exc.message}")
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": "Too many requests",
            "detail": exc.detail,
            "code": exc.error_code
        }
    )


@app.exception_handler(LLMGenerationError)
async def llm_generation_error_handler(request: Request, exc: LLMGenerationError):
    """
    AC#10: Network timeouts from Ollama handled with 503.
    Returns generic error message without exposing internal details.
    """
    logger.error(f"LLM generation error: {exc.message}")
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": "Generation failed",
            "detail": exc.detail,
            "code": exc.error_code
        }
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """
    AC#10: Database errors logged and user receives generic error message.
    No stack traces or internal details exposed.
    """
    logger.error(f"Database error: {exc.message}")
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": "Database error",
            "detail": exc.detail,
            "code": exc.error_code
        }
    )


@app.exception_handler(RetrievalServiceError)
async def retrieval_service_error_handler(request: Request, exc: RetrievalServiceError):
    """
    AC#3: Retrieval service error handling.
    """
    logger.error(f"Retrieval service error: {exc.message}")
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": "Retrieval failed",
            "detail": exc.detail,
            "code": exc.error_code
        }
    )


@app.exception_handler(IAServiceException)
async def ia_service_exception_handler(request: Request, exc: IAServiceException):
    """
    Catch-all handler for any other IA service exceptions.
    """
    logger.error(f"IA service error: {exc.message}")
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": "Service error",
            "detail": exc.detail,
            "code": exc.error_code
        }
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", version="1.0.0")