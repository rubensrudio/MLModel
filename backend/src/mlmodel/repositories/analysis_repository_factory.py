from mlmodel.core.config import Settings
from mlmodel.repositories.analysis_repository import AnalysisRepository
from mlmodel.repositories.local_analysis_repository import LocalAnalysisRepository
from mlmodel.repositories.postgres_analysis_repository import PostgresAnalysisRepository


def create_analysis_repository(settings: Settings) -> AnalysisRepository:
    if settings.should_use_postgres_for_analyses:
        database_url = settings.resolved_database_url
        if not database_url:
            raise RuntimeError(
                "PostgreSQL analysis storage requires MLMODEL_DATABASE_URL or "
                "POSTGRESQL_HOST, POSTGRESQL_USER, and POSTGRESQL_PASSWORD."
            )
        return PostgresAnalysisRepository(database_url, schema=settings.postgresql_schema_value)

    return LocalAnalysisRepository()
