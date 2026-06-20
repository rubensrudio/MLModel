from fastapi import APIRouter, Depends, HTTPException, status

from mlmodel.core.config import get_settings
from mlmodel.repositories.analysis_repository_factory import create_analysis_repository
from mlmodel.repositories.model_run_repository_factory import create_model_run_repository
from mlmodel.schemas.analyses import SavedAnalysis, SavedAnalysisCreate
from mlmodel.schemas.model_runs import ModelRun
from mlmodel.services.analysis_service import AnalysisService
from mlmodel.services.model_run_service import ModelRunService

router = APIRouter(prefix="/analyses", tags=["analyses"])


def get_analysis_service() -> AnalysisService:
    return AnalysisService(create_analysis_repository(get_settings()))


def get_model_run_service() -> ModelRunService:
    return ModelRunService(create_model_run_repository(get_settings()))


@router.post("", response_model=SavedAnalysis, status_code=status.HTTP_201_CREATED)
def create_analysis(
    request: SavedAnalysisCreate,
    service: AnalysisService = Depends(get_analysis_service),
) -> SavedAnalysis:
    return service.create_analysis(request)


@router.get("", response_model=list[SavedAnalysis])
def list_analyses(
    service: AnalysisService = Depends(get_analysis_service),
) -> list[SavedAnalysis]:
    return service.list_analyses()


@router.get("/{analysis_id}", response_model=SavedAnalysis)
def get_analysis(
    analysis_id: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> SavedAnalysis:
    analysis = service.get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' was not found.",
        )
    return analysis


@router.get("/{analysis_id}/model-runs", response_model=list[ModelRun])
def list_analysis_model_runs(
    analysis_id: str,
    service: ModelRunService = Depends(get_model_run_service),
) -> list[ModelRun]:
    return service.list_model_runs(saved_analysis_id=analysis_id)
