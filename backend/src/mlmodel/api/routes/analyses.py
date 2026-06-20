from fastapi import APIRouter, Depends, HTTPException, status

from mlmodel.repositories.analysis_repository import AnalysisRepository
from mlmodel.repositories.local_analysis_repository import LocalAnalysisRepository
from mlmodel.schemas.analyses import SavedAnalysis, SavedAnalysisCreate
from mlmodel.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyses", tags=["analyses"])


def get_analysis_service() -> AnalysisService:
    repository: AnalysisRepository = LocalAnalysisRepository()
    return AnalysisService(repository)


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
