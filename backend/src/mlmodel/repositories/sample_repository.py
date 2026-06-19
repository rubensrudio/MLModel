from typing import Protocol

from mlmodel.schemas.samples import Sample


class SampleRepository(Protocol):
    def list_samples(self) -> list[Sample]:
        """Return available petrophysical samples."""
