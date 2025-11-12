from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.auth.routes import router as auth_router
from app.auth.models import HealthResponse
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Validar configuración y crear base de datos
    settings = get_settings()
    print(f"🚀 Iniciando Asistente de Conocimiento API en modo: {settings.fastapi_env}")
    print(f"🔗 Base de datos: {settings.database_url}")
    print(f"🤖 Servidor Ollama: {settings.ollama_host}")

    # Validación completa de la configuración ya se ejecuta al importar settings
    # pero podemos agregar mensajes específicos aquí
    create_db_and_tables()
    print("✅ Base de datos inicializada correctamente")

    yield

    # Shutdown (if needed)
    print("🛑 Aplicación detenida")


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

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", version="1.0.0")