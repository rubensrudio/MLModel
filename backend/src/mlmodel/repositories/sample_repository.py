from typing import Protocol

from mlmodel.schemas.samples import Sample, SampleDetail


class SampleRepository(Protocol):
    def list_samples(self) -> list[Sample]:
        """Return available petrophysical samples."""

    def get_sample_detail(self, sample_code: str) -> SampleDetail | None:
        """Return expanded data for one petrophysical sample."""
