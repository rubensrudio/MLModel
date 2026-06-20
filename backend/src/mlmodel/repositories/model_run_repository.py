from typing import Protocol

from mlmodel.schemas.model_runs import ModelRun, ModelRunCreate


class ModelRunRepository(Protocol):
    def create_model_run(self, model_run: ModelRunCreate) -> ModelRun:
        """Persist and return a model run."""

    def list_model_runs(self, saved_analysis_id: str | None = None) -> list[ModelRun]:
        """Return model runs, optionally filtered by saved analysis."""

    def get_model_run(self, run_id: str) -> ModelRun | None:
        """Return one model run by id."""
