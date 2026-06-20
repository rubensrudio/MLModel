from fastapi import APIRouter, Depends, HTTPException, status

from mlmodel.core.config import get_settings
from mlmodel.integrations.mlflow_client import log_model_run_to_mlflow
from mlmodel.repositories.model_run_repository_factory import create_model_run_repository
from mlmodel.schemas.model_runs import GassmannModelRunRequest, ModelRun, ModelRunCreate
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
    model_run = service.get_model_run(run_id)
    if model_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model run '{run_id}' was not found.",
        )
    return model_run


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
    return _create_model_run_with_optional_mlflow(
        ModelRunCreate(
            model_name="rockphypy.gassmann",
            model_version=None,
            engine=result.engine,
            parameters=request.parameters.model_dump(mode="json"),
            result=result.model_dump(mode="json"),
            assumptions=result.assumptions,
            saved_analysis_id=request.saved_analysis_id,
        ),
        service,
    )


def _create_model_run_with_optional_mlflow(
    model_run: ModelRunCreate,
    service: ModelRunService,
) -> ModelRun:
    mlflow_run_id = log_model_run_to_mlflow(get_settings(), model_run)
    if mlflow_run_id:
        model_run = model_run.model_copy(update={"mlflow_run_id": mlflow_run_id})
    return service.create_model_run(model_run)
