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


@lru_cache
def get_settings() -> Settings:
    return Settings()
