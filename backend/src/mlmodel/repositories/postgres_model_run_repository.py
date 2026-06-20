import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mlmodel.repositories.model_run_repository import ModelRunRepository
from mlmodel.schemas.model_runs import ModelRun, ModelRunCreate


class PostgresModelRunRepository(ModelRunRepository):
    def __init__(self, database_url: str, schema: str = "public") -> None:
        self._database_url = database_url
        self._schema = _validate_identifier(schema, "PostgreSQL schema")
        self._table_name = f"{self._schema}.model_runs"
        self._ensure_schema()

    def create_model_run(self, model_run: ModelRunCreate) -> ModelRun:
        now = datetime.now(UTC)
        run_id = str(uuid4())
        payload = model_run.model_dump(mode="json")

        with self._connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {self._table_name} (
                    run_id,
                    model_name,
                    model_version,
                    engine,
                    parameters,
                    result,
                    assumptions,
                    saved_analysis_id,
                    created_at
                )
                VALUES (
                    %(run_id)s,
                    %(model_name)s,
                    %(model_version)s,
                    %(engine)s,
                    %(parameters)s,
                    %(result)s,
                    %(assumptions)s,
                    %(saved_analysis_id)s,
                    %(created_at)s
                )
                """,
                {
                    "run_id": run_id,
                    "model_name": payload["model_name"],
                    "model_version": payload["model_version"],
                    "engine": payload["engine"],
                    "parameters": _json(payload["parameters"]),
                    "result": _json(payload["result"]),
                    "assumptions": _json(payload["assumptions"]),
                    "saved_analysis_id": payload["saved_analysis_id"],
                    "created_at": now,
                },
            )
            connection.commit()

        saved = self.get_model_run(run_id)
        if saved is None:
            raise RuntimeError("Model run was not found after insert.")
        return saved

    def list_model_runs(self, saved_analysis_id: str | None = None) -> list[ModelRun]:
        with self._connect() as connection:
            if saved_analysis_id is None:
                rows = connection.execute(
                    f"""
                    SELECT
                        run_id,
                        model_name,
                        model_version,
                        engine,
                        parameters,
                        result,
                        assumptions,
                        saved_analysis_id,
                        created_at
                    FROM {self._table_name}
                    ORDER BY created_at ASC, run_id ASC
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    f"""
                    SELECT
                        run_id,
                        model_name,
                        model_version,
                        engine,
                        parameters,
                        result,
                        assumptions,
                        saved_analysis_id,
                        created_at
                    FROM {self._table_name}
                    WHERE saved_analysis_id = %(saved_analysis_id)s
                    ORDER BY created_at ASC, run_id ASC
                    """,
                    {"saved_analysis_id": saved_analysis_id},
                ).fetchall()
        return [_row_to_model_run(row) for row in rows]

    def get_model_run(self, run_id: str) -> ModelRun | None:
        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT
                    run_id,
                    model_name,
                    model_version,
                    engine,
                    parameters,
                    result,
                    assumptions,
                    saved_analysis_id,
                    created_at
                FROM {self._table_name}
                WHERE run_id = %(run_id)s
                """,
                {"run_id": run_id},
            ).fetchone()
        return _row_to_model_run(row) if row else None

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            if self._schema != "public":
                connection.execute(f"CREATE SCHEMA IF NOT EXISTS {self._schema}")
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    run_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_version TEXT,
                    engine TEXT,
                    parameters JSONB NOT NULL,
                    result JSONB NOT NULL,
                    assumptions JSONB NOT NULL DEFAULT '[]'::jsonb,
                    saved_analysis_id TEXT,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def _connect(self) -> Any:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL model run repository requires psycopg. "
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


def _row_to_model_run(row: dict[str, Any]) -> ModelRun:
    return ModelRun(
        run_id=row["run_id"],
        model_name=row["model_name"],
        model_version=row["model_version"],
        engine=row["engine"],
        parameters=row["parameters"],
        result=row["result"],
        assumptions=row["assumptions"],
        saved_analysis_id=row["saved_analysis_id"],
        created_at=row["created_at"],
    )
