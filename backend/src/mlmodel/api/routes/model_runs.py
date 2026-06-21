import csv
import json
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError

from mlmodel.core.config import get_settings
from mlmodel.integrations.mlflow_client import log_model_run_to_mlflow
from mlmodel.repositories.model_run_repository_factory import create_model_run_repository
from mlmodel.schemas.model_runs import (
    AkiRichardsModelRunRequest,
    GassmannModelRunRequest,
    GranularMediaModelRunRequest,
    ModelRun,
    ModelRunCreate,
    RockPhyPyBatchModel,
    RockPhyPyBatchModelRunRequest,
)
from mlmodel.schemas.rock_physics import AkiRichardsRequest, GassmannRequest, GranularMediaRequest
from mlmodel.services.model_run_service import ModelRunService
from mlmodel.services.rock_physics_service import RockPhysicsService

router = APIRouter(prefix="/model-runs", tags=["model runs"])


def get_model_run_service() -> ModelRunService:
    return ModelRunService(create_model_run_repository(get_settings()))


@router.post("", response_model=ModelRun, status_code=status.HTTP_201_CREATED)
def create_model_run(
    request: ModelRunCreate,
    service: ModelRunService = Depends(get_model_run_service),
) -> ModelRun:
    return _create_model_run_with_optional_mlflow(request, service)


@router.get("", response_model=list[ModelRun])
def list_model_runs(
    saved_analysis_id: str | None = None,
    service: ModelRunService = Depends(get_model_run_service),
) -> list[ModelRun]:
    return service.list_model_runs(saved_analysis_id)


@router.get("/{run_id}", response_model=ModelRun)
def get_model_run(
    run_id: str,
    service: ModelRunService = Depends(get_model_run_service),
) -> ModelRun:
    return _get_existing_model_run(run_id, service)


@router.get("/{run_id}/export/json", response_model=ModelRun)
def export_model_run_json(
    run_id: str,
    service: ModelRunService = Depends(get_model_run_service),
) -> ModelRun:
    return _get_existing_model_run(run_id, service)


@router.get("/{run_id}/export/csv")
def export_model_run_csv(
    run_id: str,
    service: ModelRunService = Depends(get_model_run_service),
) -> Response:
    model_run = _get_existing_model_run(run_id, service)
    return Response(
        content=_model_run_to_csv(model_run),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="model-run-{run_id}.csv"'},
    )


@router.post(
    "/rockphypy/gassmann",
    response_model=ModelRun,
    status_code=status.HTTP_201_CREATED,
)
def run_and_save_gassmann(
    request: GassmannModelRunRequest,
    service: ModelRunService = Depends(get_model_run_service),
) -> ModelRun:
    result = RockPhysicsService().run_gassmann(request.parameters)
    return _save_rockphypy_model_run(
        model_name="rockphypy.gassmann",
        parameters=request.parameters,
        result=result,
        saved_analysis_id=request.saved_analysis_id,
        service=service,
    )


@router.post(
    "/rockphypy/softsand",
    response_model=ModelRun,
    status_code=status.HTTP_201_CREATED,
)
def run_and_save_softsand(
    request: GranularMediaModelRunRequest,
    service: ModelRunService = Depends(get_model_run_service),
) -> ModelRun:
    result = RockPhysicsService().run_softsand(request.parameters)
    return _save_rockphypy_model_run(
        model_name="rockphypy.softsand",
        parameters=request.parameters,
        result=result,
        saved_analysis_id=request.saved_analysis_id,
        service=service,
    )


@router.post(
    "/rockphypy/stiffsand",
    response_model=ModelRun,
    status_code=status.HTTP_201_CREATED,
)
def run_and_save_stiffsand(
    request: GranularMediaModelRunRequest,
    service: ModelRunService = Depends(get_model_run_service),
) -> ModelRun:
    result = RockPhysicsService().run_stiffsand(request.parameters)
    return _save_rockphypy_model_run(
        model_name="rockphypy.stiffsand",
        parameters=request.parameters,
        result=result,
        saved_analysis_id=request.saved_analysis_id,
        service=service,
    )


@router.post(
    "/rockphypy/avo/aki-richards",
    response_model=ModelRun,
    status_code=status.HTTP_201_CREATED,
)
def run_and_save_aki_richards(
    request: AkiRichardsModelRunRequest,
    service: ModelRunService = Depends(get_model_run_service),
) -> ModelRun:
    result = RockPhysicsService().run_aki_richards(request.parameters)
    return _save_rockphypy_model_run(
        model_name="rockphypy.avo.aki_richards",
        parameters=request.parameters,
        result=result,
        saved_analysis_id=request.saved_analysis_id,
        service=service,
    )


@router.post(
    "/rockphypy/batch",
    response_model=ModelRun,
    status_code=status.HTTP_201_CREATED,
)
def run_and_save_rockphypy_batch(
    request: RockPhyPyBatchModelRunRequest,
    service: ModelRunService = Depends(get_model_run_service),
) -> ModelRun:
    input_format = "csv" if request.csv_text else "json"
    rows = _batch_rows_from_request(request)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Batch input must contain at least one row.",
        )

    result = _execute_rockphypy_batch(request.model, rows)
    return _create_model_run_with_optional_mlflow(
        ModelRunCreate(
            model_name=f"rockphypy.batch.{_batch_model_name_suffix(request.model)}",
            model_version=None,
            engine="rockphypy-batch",
            parameters={
                "model": request.model,
                "input_format": input_format,
                "row_count": len(rows),
                "rows": rows,
            },
            result=result,
            assumptions=[
                "Batch model execution",
                "Each row is validated independently",
                "Row-level failures are captured in the result payload",
            ],
            saved_analysis_id=request.saved_analysis_id,
        ),
        service,
    )


def _save_rockphypy_model_run(
    *,
    model_name: str,
    parameters: BaseModel,
    result: BaseModel,
    saved_analysis_id: str | None,
    service: ModelRunService,
) -> ModelRun:
    return _create_model_run_with_optional_mlflow(
        ModelRunCreate(
            model_name=model_name,
            model_version=None,
            engine=result.engine,
            parameters=parameters.model_dump(mode="json"),
            result=result.model_dump(mode="json"),
            assumptions=result.assumptions,
            saved_analysis_id=saved_analysis_id,
        ),
        service,
    )


def _batch_rows_from_request(request: RockPhyPyBatchModelRunRequest) -> list[dict[str, Any]]:
    if request.rows is not None:
        return request.rows
    if request.csv_text is None:
        return []

    reader = csv.DictReader(StringIO(request.csv_text.strip()))
    return [
        {key: value for key, value in row.items() if key is not None}
        for row in reader
    ]


def _execute_rockphypy_batch(
    model: RockPhyPyBatchModel,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    service = RockPhysicsService()
    schema_type, runner = _batch_model_contract(model, service)
    batch_rows = []

    for index, row in enumerate(rows):
        normalized_row = _normalize_batch_row(model, row)
        try:
            parameters = schema_type.model_validate(normalized_row)
            result = runner(parameters)
        except ValidationError as exc:
            batch_rows.append(
                {
                    "row_index": index,
                    "status": "error",
                    "parameters": normalized_row,
                    "error": exc.errors(),
                }
            )
            continue

        batch_rows.append(
            {
                "row_index": index,
                "status": "success",
                "parameters": parameters.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
            }
        )

    successful_count = sum(1 for row in batch_rows if row["status"] == "success")
    failed_count = len(batch_rows) - successful_count
    return {
        "model": model,
        "row_count": len(batch_rows),
        "successful_count": successful_count,
        "failed_count": failed_count,
        "rows": batch_rows,
    }


def _batch_model_contract(
    model: RockPhyPyBatchModel,
    service: RockPhysicsService,
):
    if model == "gassmann":
        return GassmannRequest, service.run_gassmann
    if model == "softsand":
        return GranularMediaRequest, service.run_softsand
    if model == "stiffsand":
        return GranularMediaRequest, service.run_stiffsand
    return AkiRichardsRequest, service.run_aki_richards


def _normalize_batch_row(model: RockPhyPyBatchModel, row: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        key: value
        for key, value in row.items()
        if value is not None and value != ""
    }
    if model == "avo.aki-richards":
        angles = normalized.get("incident_angles_degrees")
        if isinstance(angles, str):
            separator = ";" if ";" in angles else ","
            normalized["incident_angles_degrees"] = [
                angle.strip()
                for angle in angles.split(separator)
                if angle.strip()
            ]
    return normalized


def _batch_model_name_suffix(model: RockPhyPyBatchModel) -> str:
    if model == "avo.aki-richards":
        return "avo.aki_richards"
    return model


def _create_model_run_with_optional_mlflow(
    model_run: ModelRunCreate,
    service: ModelRunService,
) -> ModelRun:
    try:
        mlflow_run_id = log_model_run_to_mlflow(get_settings(), model_run)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if mlflow_run_id:
        model_run = model_run.model_copy(update={"mlflow_run_id": mlflow_run_id})
    return service.create_model_run(model_run)


def _get_existing_model_run(run_id: str, service: ModelRunService) -> ModelRun:
    model_run = service.get_model_run(run_id)
    if model_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model run '{run_id}' was not found.",
        )
    return model_run


def _model_run_to_csv(model_run: ModelRun) -> str:
    if _is_batch_model_run(model_run):
        rows = [
            _flatten_batch_row(model_run, row)
            for row in model_run.result.get("rows", [])
        ]
    else:
        rows = [_flatten_simple_model_run(model_run)]

    return _rows_to_csv(rows)


def _is_batch_model_run(model_run: ModelRun) -> bool:
    return (
        model_run.model_name.startswith("rockphypy.batch.")
        and isinstance(model_run.result.get("rows"), list)
    )


def _flatten_simple_model_run(model_run: ModelRun) -> dict[str, Any]:
    row: dict[str, Any] = {
        "run_id": model_run.run_id,
        "created_at": model_run.created_at.isoformat(),
        "model_name": model_run.model_name,
        "model_version": model_run.model_version,
        "engine": model_run.engine,
        "saved_analysis_id": model_run.saved_analysis_id,
        "mlflow_run_id": model_run.mlflow_run_id,
    }
    _flatten_mapping("parameters", model_run.parameters, row)
    _flatten_mapping("result", model_run.result, row)
    if model_run.assumptions:
        row["assumptions"] = json.dumps(model_run.assumptions, ensure_ascii=True)
    return row


def _flatten_batch_row(model_run: ModelRun, batch_row: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "run_id": model_run.run_id,
        "created_at": model_run.created_at.isoformat(),
        "model_name": model_run.model_name,
        "engine": model_run.engine,
        "saved_analysis_id": model_run.saved_analysis_id,
        "mlflow_run_id": model_run.mlflow_run_id,
        "batch_model": model_run.result.get("model"),
        "row_index": batch_row.get("row_index"),
        "status": batch_row.get("status"),
    }
    _flatten_mapping("parameters", batch_row.get("parameters", {}), row)
    _flatten_mapping("result", batch_row.get("result", {}), row)
    if "error" in batch_row:
        row["error"] = json.dumps(batch_row["error"], ensure_ascii=True)
    return row


def _flatten_mapping(prefix: str, value: Any, row: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        return

    for key, nested_value in value.items():
        column = f"{prefix}.{key}"
        if isinstance(nested_value, dict):
            _flatten_mapping(column, nested_value, row)
        elif isinstance(nested_value, list):
            row[column] = json.dumps(nested_value, ensure_ascii=True)
        else:
            row[column] = nested_value


def _rows_to_csv(rows: list[dict[str, Any]]) -> str:
    fieldnames = sorted({fieldname for row in rows for fieldname in row})
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
