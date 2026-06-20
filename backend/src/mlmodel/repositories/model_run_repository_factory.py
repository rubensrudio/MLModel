from mlmodel.core.config import Settings
from mlmodel.repositories.local_model_run_repository import LocalModelRunRepository
from mlmodel.repositories.model_run_repository import ModelRunRepository
from mlmodel.repositories.postgres_model_run_repository import PostgresModelRunRepository


def create_model_run_repository(settings: Settings) -> ModelRunRepository:
    if settings.should_use_postgres_for_analyses:
        database_url = settings.resolved_database_url
        if not database_url:
            raise RuntimeError(
                "PostgreSQL model run storage requires MLMODEL_DATABASE_URL or "
                "POSTGRESQL_HOST, POSTGRESQL_USER, and POSTGRESQL_PASSWORD."
            )
        return PostgresModelRunRepository(database_url, schema=settings.postgresql_schema_value)

    return LocalModelRunRepository()
