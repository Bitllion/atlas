from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    app_name: str = "Atlas API"
    database_url: str = Field(
        default="postgresql+psycopg://atlas:atlas@localhost:55433/atlas",
        validation_alias=AliasChoices("DATABASE_URL", "ATLAS_DATABASE_URL"),
    )
    log_level: str = "INFO"
    upload_dir: str = "uploads"
    auth_mode: str = "dev"
    jwt_secret: str = "atlas-development-secret-change-me"
    auth_token_expire_minutes: int = 12 * 60
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
