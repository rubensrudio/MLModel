from fastapi import APIRouter, Depends

from mlmodel.repositories.local_sample_repository import LocalSampleRepository
from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.analytics import CrossplotRequest, CrossplotResponse
from mlmodel.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service() -> AnalyticsService:
    repository: SampleRepository = LocalSampleRepository()
    return AnalyticsService(repository)


@router.post("/crossplot", response_model=CrossplotResponse)
def create_crossplot(
    request: CrossplotRequest,
    service: AnalyticsService = Depends(get_analytics_service),
) -> CrossplotResponse:
    return service.create_crossplot(request)
