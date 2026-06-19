from fastapi import APIRouter, Depends

from mlmodel.repositories.local_sample_repository import LocalSampleRepository
from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.analytics import (
    BoxplotRequest,
    BoxplotResponse,
    CrossplotRequest,
    CrossplotResponse,
    HistogramRequest,
    HistogramResponse,
)
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


@router.post("/histogram", response_model=HistogramResponse)
def create_histogram(
    request: HistogramRequest,
    service: AnalyticsService = Depends(get_analytics_service),
) -> HistogramResponse:
    return service.create_histogram(request)


@router.post("/boxplot", response_model=BoxplotResponse)
def create_boxplot(
    request: BoxplotRequest,
    service: AnalyticsService = Depends(get_analytics_service),
) -> BoxplotResponse:
    return service.create_boxplot(request)
