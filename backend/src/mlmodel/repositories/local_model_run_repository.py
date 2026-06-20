from datetime import UTC, datetime
from uuid import uuid4

from mlmodel.repositories.model_run_repository import ModelRunRepository
from mlmodel.schemas.model_runs import ModelRun, ModelRunCreate

_MODEL_RUNS: dict[str, ModelRun] = {}


class LocalModelRunRepository(ModelRunRepository):
    def create_model_run(self, model_run: ModelRunCreate) -> ModelRun:
        saved_model_run = ModelRun(
            **model_run.model_dump(),
            run_id=str(uuid4()),
            created_at=datetime.now(UTC),
        )
        _MODEL_RUNS[saved_model_run.run_id] = saved_model_run
        return saved_model_run

    def list_model_runs(self, saved_analysis_id: str | None = None) -> list[ModelRun]:
        model_runs = sorted(_MODEL_RUNS.values(), key=lambda model_run: model_run.created_at)
        if saved_analysis_id is None:
            return model_runs
        return [
            model_run
            for model_run in model_runs
            if model_run.saved_analysis_id == saved_analysis_id
        ]

    def get_model_run(self, run_id: str) -> ModelRun | None:
        return _MODEL_RUNS.get(run_id)
