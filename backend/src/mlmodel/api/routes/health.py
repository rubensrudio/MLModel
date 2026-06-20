from fastapi import APIRouter

from mlmodel.core.config import get_settings
from mlmodel.repositories.postgres_analysis_repository import PostgresAnalysisRepository
from mlmodel.schemas.health import HealthResponse
from mlmodel.schemas.persistence import PersistenceHealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get("/health/persistence", response_model=PersistenceHealthResponse)
def persistence_health_check() -> PersistenceHealthResponse:
    settings = get_settings()
    database_url = settings.resolved_database_url
    backend = "postgres" if settings.should_use_postgres_for_analyses else "local"

    if backend != "postgres" or not database_url:
        return PersistenceHealthResponse(
            backend=backend,
            database_url_configured=settings.database_url is not None,
            postgresql_host_configured=settings.postgresql_host_value is not None,
            postgresql_database=settings.postgresql_database_value,
            postgresql_schema=settings.postgresql_schema_value,
            table_name="saved_analyses",
            table_exists=None,
        )

    try:
        health = PostgresAnalysisRepository(
            database_url,
            schema=settings.postgresql_schema_value,
        ).get_health()
    except Exception as exc:
        return PersistenceHealthResponse(
            backend=backend,
            database_url_configured=settings.database_url is not None,
            postgresql_host_configured=settings.postgresql_host_value is not None,
            postgresql_database=settings.postgresql_database_value,
            postgresql_schema=settings.postgresql_schema_value,
            table_name="saved_analyses",
            table_exists=False,
            error=str(exc),
        )

    return PersistenceHealthResponse(
        backend=backend,
        database_url_configured=settings.database_url is not None,
        postgresql_host_configured=settings.postgresql_host_value is not None,
        postgresql_database=settings.postgresql_database_value,
        postgresql_schema=settings.postgresql_schema_value,
        table_name="saved_analyses",
        table_exists=health["table_exists"],
        current_database=health["current_database"],
        current_schema=health["current_schema"],
    )
