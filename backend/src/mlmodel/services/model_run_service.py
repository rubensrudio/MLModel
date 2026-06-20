from mlmodel.repositories.model_run_repository import ModelRunRepository
from mlmodel.schemas.model_runs import ModelRun, ModelRunCreate


class ModelRunService:
    def __init__(self, repository: ModelRunRepository) -> None:
        self._repository = repository

    def create_model_run(self, model_run: ModelRunCreate) -> ModelRun:
        return self._repository.create_model_run(model_run)

    def list_model_runs(self, saved_analysis_id: str | None = None) -> list[ModelRun]:
        return self._repository.list_model_runs(saved_analysis_id)

    def get_model_run(self, run_id: str) -> ModelRun | None:
        return self._repository.get_model_run(run_id)
