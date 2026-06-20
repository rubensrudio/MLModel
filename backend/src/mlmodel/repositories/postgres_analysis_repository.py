import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mlmodel.repositories.analysis_repository import AnalysisRepository
from mlmodel.schemas.analyses import SavedAnalysis, SavedAnalysisCreate


class PostgresAnalysisRepository(AnalysisRepository):
    def __init__(self, database_url: str, schema: str = "public") -> None:
        self._database_url = database_url
        self._schema = _validate_identifier(schema, "PostgreSQL schema")
        self._table_name = f"{self._schema}.saved_analyses"
        self._ensure_schema()

    def create_analysis(self, analysis: SavedAnalysisCreate) -> SavedAnalysis:
        now = datetime.now(UTC)
        analysis_id = str(uuid4())
        payload = analysis.model_dump(mode="json")

        with self._connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {self._table_name} (
                    analysis_id,
                    title,
                    analysis_type,
                    configuration,
                    comments,
                    selected_models,
                    result,
                    created_at,
                    updated_at
                )
                VALUES (
                    %(analysis_id)s,
                    %(title)s,
                    %(analysis_type)s,
                    %(configuration)s,
                    %(comments)s,
                    %(selected_models)s,
                    %(result)s,
                    %(created_at)s,
                    %(updated_at)s
                )
                """,
                {
                    "analysis_id": analysis_id,
                    "title": payload["title"],
                    "analysis_type": payload["analysis_type"],
                    "configuration": _json(payload["configuration"]),
                    "comments": _json(payload["comments"]),
                    "selected_models": _json(payload["selected_models"]),
                    "result": _json(payload["result"]),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            connection.commit()

        saved = self.get_analysis(analysis_id)
        if saved is None:
            raise RuntimeError("Saved analysis was not found after insert.")
        return saved

    def list_analyses(self) -> list[SavedAnalysis]:
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    analysis_id,
                    title,
                    analysis_type,
                    configuration,
                    comments,
                    selected_models,
                    result,
                    created_at,
                    updated_at
                FROM {self._table_name}
                ORDER BY created_at ASC, analysis_id ASC
                """
            ).fetchall()
        return [_row_to_saved_analysis(row) for row in rows]

    def get_analysis(self, analysis_id: str) -> SavedAnalysis | None:
        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT
                    analysis_id,
                    title,
                    analysis_type,
                    configuration,
                    comments,
                    selected_models,
                    result,
                    created_at,
                    updated_at
                FROM {self._table_name}
                WHERE analysis_id = %(analysis_id)s
                """,
                {"analysis_id": analysis_id},
            ).fetchone()
        return _row_to_saved_analysis(row) if row else None

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            if self._schema != "public":
                connection.execute(
                    f"CREATE SCHEMA IF NOT EXISTS {self._schema}"
                )
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    analysis_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    configuration JSONB NOT NULL,
                    comments JSONB NOT NULL DEFAULT '[]'::jsonb,
                    selected_models JSONB NOT NULL DEFAULT '[]'::jsonb,
                    result JSONB,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def get_health(self) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    current_database() AS current_database,
                    current_schema() AS current_schema,
                    EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = %(schema)s
                          AND table_name = 'saved_analyses'
                    ) AS table_exists
                """,
                {"schema": self._schema},
            ).fetchone()
        return dict(row)

    def _connect(self) -> Any:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL analysis repository requires psycopg. "
                "Install backend dependencies with `python -m pip install -e .`."
            ) from exc

        return psycopg.connect(self._database_url, row_factory=dict_row)


def _json(value: Any) -> Any:
    try:
        from psycopg.types.json import Jsonb
    except ImportError as exc:
        raise RuntimeError("PostgreSQL JSON support requires psycopg.") from exc
    return Jsonb(value)


def _validate_identifier(value: str, label: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"{label} must be a simple SQL identifier.")
    return value


def _row_to_saved_analysis(row: dict[str, Any]) -> SavedAnalysis:
    return SavedAnalysis(
        analysis_id=row["analysis_id"],
        title=row["title"],
        analysis_type=row["analysis_type"],
        configuration=row["configuration"],
        comments=row["comments"],
        selected_models=row["selected_models"],
        result=row["result"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
