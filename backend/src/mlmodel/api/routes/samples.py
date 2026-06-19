from fastapi import APIRouter, Depends, HTTPException, Query, status

from mlmodel.repositories.local_sample_repository import LocalSampleRepository
from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.filters import SampleFilters
from mlmodel.schemas.samples import Sample, SampleDetail, SamplesSummary
from mlmodel.services.sample_service import SampleService

router = APIRouter(prefix="/samples", tags=["samples"])


def get_sample_service() -> SampleService:
    repository: SampleRepository = LocalSampleRepository()
    return SampleService(repository)


def get_sample_filters(
    sample_codes: list[str] | None = Query(default=None),
    wells: list[str] | None = Query(default=None),
    rock_types: list[str] | None = Query(default=None),
    lithologies: list[str] | None = Query(default=None),
    min_depth_m: float | None = Query(default=None, ge=0),
    max_depth_m: float | None = Query(default=None, ge=0),
    min_porosity_percent: float | None = Query(default=None, ge=0, le=100),
    max_porosity_percent: float | None = Query(default=None, ge=0, le=100),
    min_confining_pressure_psi: float | None = Query(default=None, ge=0),
    max_confining_pressure_psi: float | None = Query(default=None, ge=0),
) -> SampleFilters:
    return SampleFilters(
        sample_codes=_split_query_values(sample_codes),
        wells=_split_query_values(wells),
        rock_types=_split_query_values(rock_types),
        lithologies=_split_query_values(lithologies),
        min_depth_m=min_depth_m,
        max_depth_m=max_depth_m,
        min_porosity_percent=min_porosity_percent,
        max_porosity_percent=max_porosity_percent,
        min_confining_pressure_psi=min_confining_pressure_psi,
        max_confining_pressure_psi=max_confining_pressure_psi,
    )


@router.get("", response_model=list[Sample])
def list_samples(
    service: SampleService = Depends(get_sample_service),
    filters: SampleFilters = Depends(get_sample_filters),
) -> list[Sample]:
    return service.list_samples(filters)


@router.get("/summary", response_model=SamplesSummary)
def get_samples_summary(
    service: SampleService = Depends(get_sample_service),
    filters: SampleFilters = Depends(get_sample_filters),
) -> SamplesSummary:
    return service.get_summary(filters)


@router.get("/{sample_code}", response_model=SampleDetail)
def get_sample_detail(
    sample_code: str,
    service: SampleService = Depends(get_sample_service),
) -> SampleDetail:
    detail = service.get_sample_detail(sample_code)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample '{sample_code}' was not found.",
        )
    return detail


def _split_query_values(values: list[str] | None) -> list[str] | None:
    if not values:
        return None

    split_values = [
        item.strip()
        for value in values
        for item in value.split(",")
        if item.strip()
    ]
    return split_values or None
