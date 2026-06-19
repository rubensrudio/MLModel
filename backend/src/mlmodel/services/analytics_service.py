from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.analytics import CrossplotPoint, CrossplotRequest, CrossplotResponse
from mlmodel.schemas.samples import Sample


class AnalyticsService:
    def __init__(self, repository: SampleRepository) -> None:
        self._repository = repository

    def create_crossplot(self, request: CrossplotRequest) -> CrossplotResponse:
        samples = self._repository.list_samples()
        return CrossplotResponse(
            x_field=request.x_field,
            y_field=request.y_field,
            color_by=request.color_by,
            points=[
                CrossplotPoint(
                    sample_code=sample.sample_code,
                    x=_numeric_value(sample, request.x_field),
                    y=_numeric_value(sample, request.y_field),
                    color=_category_value(sample, request.color_by) if request.color_by else None,
                )
                for sample in samples
            ],
        )


def _numeric_value(sample: Sample, field: str) -> float:
    if field == "porosity_percent":
        return sample.porosity_fraction * 100
    return float(getattr(sample, field))


def _category_value(sample: Sample, field: str) -> str:
    return str(getattr(sample, field))
