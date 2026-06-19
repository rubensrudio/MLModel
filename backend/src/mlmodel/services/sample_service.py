from statistics import fmean

from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.filters import SampleFilters
from mlmodel.schemas.samples import Sample, SampleDetail, SamplesSummary
from mlmodel.services.sample_filter import filter_samples


class SampleService:
    def __init__(self, repository: SampleRepository) -> None:
        self._repository = repository

    def list_samples(self, filters: SampleFilters | None = None) -> list[Sample]:
        return filter_samples(self._repository.list_samples(), filters)

    def get_sample_detail(self, sample_code: str) -> SampleDetail | None:
        return self._repository.get_sample_detail(sample_code)

    def get_summary(self, filters: SampleFilters | None = None) -> SamplesSummary:
        samples = self.list_samples(filters)
        if not samples:
            return SamplesSummary(
                sample_count=0,
                well_count=0,
                rock_type_count=0,
                min_depth_m=None,
                max_depth_m=None,
                average_porosity_percent=None,
                average_vp_m_s=None,
            )

        depths = [sample.depth_m for sample in samples]
        wells = {sample.well for sample in samples}
        rock_types = {sample.rock_type for sample in samples}

        return SamplesSummary(
            sample_count=len(samples),
            well_count=len(wells),
            rock_type_count=len(rock_types),
            min_depth_m=min(depths),
            max_depth_m=max(depths),
            average_porosity_percent=fmean(sample.porosity_fraction for sample in samples) * 100,
            average_vp_m_s=fmean(sample.vp_m_s for sample in samples),
        )
