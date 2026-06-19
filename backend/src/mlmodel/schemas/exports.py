from pydantic import BaseModel, Field

from mlmodel.schemas.filters import SampleFilters
from mlmodel.schemas.samples import Sample


class SamplesExportRequest(BaseModel):
    filters: SampleFilters | None = None


class SamplesJsonExportResponse(BaseModel):
    row_count: int = Field(ge=0)
    rows: list[Sample]
