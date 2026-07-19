from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agent Workflow Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/agent_workflow"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="AWP_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
