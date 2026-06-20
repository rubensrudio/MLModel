from functools import lru_cache
from os import getenv
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MLModel API"
    app_version: str = "0.1.0"
    environment: str = "local"
    analysis_repository_backend: Literal["auto", "local", "postgres"] = "auto"
    database_url: str | None = None
    postgresql_host: str | None = Field(default=None, validation_alias="POSTGRESQL_HOST")
    postgresql_port: int = Field(default=5432, validation_alias="POSTGRESQL_PORT")
    postgresql_user: str | None = Field(default=None, validation_alias="POSTGRESQL_USER")
    postgresql_password: str | None = Field(default=None, validation_alias="POSTGRESQL_PASSWORD")
    postgresql_database: str = "mlmodel"
    postgresql_schema: str = "public"
    mlflow_tracking_uri: str | None = None
    mlflow_experiment_name: str = "MLModel Rock Physics"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MLMODEL_",
        extra="ignore",
    )

    @property
    def resolved_database_url(self) -> str | None:
        if self.database_url:
            return self.database_url

        if not self.postgresql_host_value:
            return None
        if not self.postgresql_user_value or self.postgresql_password_value is None:
            return None

        user = quote_plus(self.postgresql_user_value)
        password = quote_plus(self.postgresql_password_value)
        database = quote_plus(self.postgresql_database_value)
        return (
            f"postgresql://{user}:{password}"
            f"@{self.postgresql_host_value}:{self.postgresql_port_value}/{database}"
        )

    @property
    def should_use_postgres_for_analyses(self) -> bool:
        if self.analysis_repository_backend == "postgres":
            return True
        if self.analysis_repository_backend == "local":
            return False
        return self.resolved_database_url is not None

    @property
    def postgresql_host_value(self) -> str | None:
        return self.postgresql_host or getenv("POSTGRESQL_HOST")

    @property
    def postgresql_port_value(self) -> int:
        return int(getenv("POSTGRESQL_PORT") or self.postgresql_port)

    @property
    def postgresql_user_value(self) -> str | None:
        return self.postgresql_user or getenv("POSTGRESQL_USER")

    @property
    def postgresql_password_value(self) -> str | None:
        if self.postgresql_password is not None:
            return self.postgresql_password
        return getenv("POSTGRESQL_PASSWORD")

    @property
    def postgresql_database_value(self) -> str:
        return self.postgresql_database

    @property
    def postgresql_schema_value(self) -> str:
        return self.postgresql_schema


@lru_cache
def get_settings() -> Settings:
    return Settings()
