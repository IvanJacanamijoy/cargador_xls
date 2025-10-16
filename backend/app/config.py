from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Base
    APP_NAME: str = "Bulk Upload API"
    DEBUG: bool = False

    # Database
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "password"
    DATABASE_NAME: str = "bulk_upload_db"

    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    CHUNK_SIZE: int = 500  # Registros por lote

    # Frontend API
    VITE_API_URL: str = Field(..., alias="VITE_API_URL")

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

def get_database_url() -> str:
    settings = get_settings()
    return (
        f"mysql+mysqlconnector://{settings.DATABASE_USER}:"
        f"{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:"
        f"{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    )
