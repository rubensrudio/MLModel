from statistics import fmean

from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.samples import Sample, SamplesSummary


class SampleService:
    def __init__(self, repository: SampleRepository) -> None:
        self._repository = repository

    def list_samples(self) -> list[Sample]:
        return self._repository.list_samples()

    def get_summary(self) -> SamplesSummary:
        samples = self.list_samples()
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
