"""Orchnii tohirgoo. .env file esvel environment variable-aas unshina."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Logistics ERP"
    DATABASE_URL: str = "sqlite:///./erp.db"  # prod: postgresql+psycopg://user:pw@host/db
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    JWT_ALGORITHM: str = "HS256"

    # Anhnii admin (users hooson baival uusgene)
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "admin12345"

<<<<<<< HEAD
    # Vite dev server-uud (orders: 5174, finance: 5173). Taslalaar tusgaarlana.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"

=======
>>>>>>> d36e373445a18be1206c41ef792e8f2f518f4cd4

@lru_cache
def get_settings() -> Settings:
    return Settings()
