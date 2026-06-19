from fastapi import APIRouter, Depends

from mlmodel.repositories.local_sample_repository import LocalSampleRepository
from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.samples import Sample, SamplesSummary
from mlmodel.services.sample_service import SampleService

router = APIRouter(prefix="/samples", tags=["samples"])


def get_sample_service() -> SampleService:
    repository: SampleRepository = LocalSampleRepository()
    return SampleService(repository)


@router.get("", response_model=list[Sample])
def list_samples(service: SampleService = Depends(get_sample_service)) -> list[Sample]:
    return service.list_samples()


@router.get("/summary", response_model=SamplesSummary)
def get_samples_summary(service: SampleService = Depends(get_sample_service)) -> SamplesSummary:
    return service.get_summary()
