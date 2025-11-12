from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Security Configuration
    secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Database
    database_url: str = "sqlite:///./database.db"

    # Ollama / LLM Configuration
    ollama_host: Optional[str] = "http://localhost:11434"
    ollama_model: Optional[str] = "llama3.1:8b-instruct-q4_K_M"

    # Development Settings
    debug: Optional[bool] = False
    log_level: Optional[str] = "info"

    # CORS Settings
    allowed_origins: Optional[str] = "http://localhost:5173,http://127.0.0.1:5173"

settings = Settings()