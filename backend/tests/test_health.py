from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from mlmodel.core.config import get_settings
from mlmodel.main import create_app

POSTGRES_ENV_KEYS = [
    "POSTGRESQL_HOST",
    "POSTGRESQL_PORT",
    "POSTGRESQL_USER",
    "POSTGRESQL_PASSWORD",
    "POSTGRESQL_DATABASE",
    "POSTGRESQL_SCHEMA",
]


def test_health_check_returns_service_status(monkeypatch: MonkeyPatch) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MLMODEL_ANALYSIS_REPOSITORY_BACKEND", "local")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "MLModel API",
        "version": "0.1.0",
    }


def test_persistence_health_returns_local_status(monkeypatch: MonkeyPatch) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MLMODEL_ANALYSIS_REPOSITORY_BACKEND", "local")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/health/persistence")

    assert response.status_code == 200
    assert response.json() == {
        "backend": "local",
        "database_url_configured": False,
        "postgresql_host_configured": False,
        "postgresql_database": "mlmodel",
        "postgresql_schema": "public",
        "table_name": "saved_analyses",
        "table_exists": None,
        "current_database": None,
        "current_schema": None,
        "error": None,
    }
