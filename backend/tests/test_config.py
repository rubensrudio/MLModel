from pytest import MonkeyPatch

from mlmodel.core.config import Settings
from mlmodel.repositories.analysis_repository_factory import create_analysis_repository
from mlmodel.repositories.local_analysis_repository import LocalAnalysisRepository

POSTGRES_ENV_KEYS = [
    "POSTGRESQL_HOST",
    "POSTGRESQL_PORT",
    "POSTGRESQL_USER",
    "POSTGRESQL_PASSWORD",
    "POSTGRESQL_DATABASE",
    "POSTGRESQL_SCHEMA",
    "MLMODEL_POSTGRESQL_DATABASE",
    "MLMODEL_POSTGRESQL_SCHEMA",
]


def test_settings_default_to_local_analysis_repository(monkeypatch: MonkeyPatch) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = Settings()

    assert settings.analysis_repository_backend == "auto"
    assert settings.database_url is None
    assert settings.resolved_database_url is None
    assert settings.should_use_postgres_for_analyses is False


def test_settings_accept_postgres_analysis_repository(monkeypatch: MonkeyPatch) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(
        analysis_repository_backend="postgres",
        database_url="postgresql://mlmodel:mlmodel@localhost:5432/mlmodel",
    )

    assert settings.analysis_repository_backend == "postgres"
    assert settings.database_url == "postgresql://mlmodel:mlmodel@localhost:5432/mlmodel"
    assert settings.resolved_database_url == "postgresql://mlmodel:mlmodel@localhost:5432/mlmodel"
    assert settings.should_use_postgres_for_analyses is True


def test_settings_build_database_url_from_postgresql_env_values(monkeypatch: MonkeyPatch) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(
        analysis_repository_backend="postgres",
        POSTGRESQL_HOST="db.example.local",
        POSTGRESQL_PORT=15432,
        POSTGRESQL_USER="ml user",
        POSTGRESQL_PASSWORD="p@ss word",
        postgresql_database="lab data",
    )

    assert settings.resolved_database_url == (
        "postgresql://ml+user:p%40ss+word@db.example.local:15432/lab+data"
    )
    assert settings.should_use_postgres_for_analyses is True


def test_settings_reads_database_url_from_postgresql_environment(
    monkeypatch: MonkeyPatch,
) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("POSTGRESQL_HOST", "db.runtime.local")
    monkeypatch.setenv("POSTGRESQL_PORT", "25432")
    monkeypatch.setenv("POSTGRESQL_USER", "runtime_user")
    monkeypatch.setenv("POSTGRESQL_PASSWORD", "runtime_secret")
    monkeypatch.setenv("POSTGRESQL_DATABASE", "wrong_global_db")

    settings = Settings()

    assert settings.resolved_database_url == (
        "postgresql://runtime_user:runtime_secret@db.runtime.local:25432/mlmodel"
    )
    assert settings.should_use_postgres_for_analyses is True


def test_settings_reads_database_override_from_mlmodel_environment(
    monkeypatch: MonkeyPatch,
) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("POSTGRESQL_HOST", "db.runtime.local")
    monkeypatch.setenv("POSTGRESQL_PORT", "25432")
    monkeypatch.setenv("POSTGRESQL_USER", "runtime_user")
    monkeypatch.setenv("POSTGRESQL_PASSWORD", "runtime_secret")
    monkeypatch.setenv("MLMODEL_POSTGRESQL_DATABASE", "runtime_db")

    settings = Settings()

    assert settings.resolved_database_url == (
        "postgresql://runtime_user:runtime_secret@db.runtime.local:25432/runtime_db"
    )


def test_settings_can_force_local_even_with_postgresql_env_values(monkeypatch: MonkeyPatch) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(
        analysis_repository_backend="local",
        POSTGRESQL_HOST="db.example.local",
        POSTGRESQL_PORT=15432,
        POSTGRESQL_USER="mlmodel",
        POSTGRESQL_PASSWORD="secret",
    )

    assert settings.resolved_database_url == (
        "postgresql://mlmodel:secret@db.example.local:15432/mlmodel"
    )
    assert settings.should_use_postgres_for_analyses is False


def test_analysis_repository_factory_uses_local_without_postgresql_config(
    monkeypatch: MonkeyPatch,
) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    repository = create_analysis_repository(Settings())

    assert isinstance(repository, LocalAnalysisRepository)
