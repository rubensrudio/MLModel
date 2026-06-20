from numbers import Number
from typing import Any

from mlmodel.core.config import Settings
from mlmodel.schemas.model_runs import ModelRunCreate


def log_model_run_to_mlflow(settings: Settings, model_run: ModelRunCreate) -> str | None:
    if not settings.mlflow_tracking_uri:
        return None

    try:
        import mlflow
    except ImportError as exc:
        raise RuntimeError(
            "MLflow logging requires mlflow. Install backend dependencies with "
            "`python -m pip install -e .`."
        ) from exc

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)

    with mlflow.start_run(run_name=model_run.model_name) as run:
        mlflow.set_tag("mlmodel.model_name", model_run.model_name)
        if model_run.model_version:
            mlflow.set_tag("mlmodel.model_version", model_run.model_version)
        if model_run.engine:
            mlflow.set_tag("mlmodel.engine", model_run.engine)
        if model_run.saved_analysis_id:
            mlflow.set_tag("mlmodel.saved_analysis_id", model_run.saved_analysis_id)

        _log_params(mlflow, model_run.parameters)
        _log_metrics(mlflow, model_run.result)
        mlflow.log_dict(model_run.model_dump(mode="json"), "model_run.json")
        return str(run.info.run_id)


def _log_params(mlflow: Any, parameters: dict[str, Any]) -> None:
    for key, value in parameters.items():
        if isinstance(value, dict | list):
            continue
        mlflow.log_param(key, value)


def _log_metrics(mlflow: Any, result: dict[str, Any]) -> None:
    for key, value in result.items():
        if isinstance(value, Number) and not isinstance(value, bool):
            mlflow.log_metric(key, float(value))
