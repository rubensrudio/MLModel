import csv
from io import StringIO

from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.analytics import (
    BoxplotRequest,
    BoxplotResponse,
    CrossplotRequest,
    CrossplotResponse,
    HistogramRequest,
    HistogramResponse,
)
from mlmodel.schemas.exports import SamplesExportRequest, SamplesJsonExportResponse
from mlmodel.schemas.samples import Sample
from mlmodel.services.analytics_service import AnalyticsService
from mlmodel.services.sample_filter import filter_samples


class ExportService:
    def __init__(self, repository: SampleRepository) -> None:
        self._repository = repository
        self._analytics_service = AnalyticsService(repository)

    def export_samples_json(self, request: SamplesExportRequest) -> SamplesJsonExportResponse:
        rows = filter_samples(self._repository.list_samples(), request.filters)
        return SamplesJsonExportResponse(row_count=len(rows), rows=rows)

    def export_samples_csv(self, request: SamplesExportRequest) -> str:
        rows = filter_samples(self._repository.list_samples(), request.filters)
        return _samples_to_csv(rows)

    def export_crossplot_json(self, request: CrossplotRequest) -> CrossplotResponse:
        return self._analytics_service.create_crossplot(request)

    def export_crossplot_csv(self, request: CrossplotRequest) -> str:
        response = self.export_crossplot_json(request)
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["sample_code", "x", "y", "color"],
            lineterminator="\n",
        )
        writer.writeheader()
        for point in response.points:
            writer.writerow(point.model_dump())
        return output.getvalue()

    def export_histogram_json(self, request: HistogramRequest) -> HistogramResponse:
        return self._analytics_service.create_histogram(request)

    def export_histogram_csv(self, request: HistogramRequest) -> str:
        response = self.export_histogram_json(request)
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["group", "start", "end", "count"],
            lineterminator="\n",
        )
        writer.writeheader()

        if response.series:
            for series in response.series:
                for bin_ in series.bins:
                    writer.writerow({"group": series.group, **bin_.model_dump()})
        else:
            for bin_ in response.bins:
                writer.writerow({"group": None, **bin_.model_dump()})
        return output.getvalue()

    def export_boxplot_json(self, request: BoxplotRequest) -> BoxplotResponse:
        return self._analytics_service.create_boxplot(request)

    def export_boxplot_csv(self, request: BoxplotRequest) -> str:
        response = self.export_boxplot_json(request)
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "group",
                "count",
                "minimum",
                "q1",
                "median",
                "q3",
                "maximum",
                "mean",
                "standard_deviation",
                "coefficient_variation_percent",
                "p10",
                "p50",
                "p90",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for series in response.series:
            writer.writerow(
                {
                    "group": series.group,
                    "count": series.count,
                    "minimum": series.minimum,
                    "q1": series.q1,
                    "median": series.median,
                    "q3": series.q3,
                    "maximum": series.maximum,
                    "mean": series.mean,
                    "standard_deviation": series.stats.standard_deviation,
                    "coefficient_variation_percent": series.stats.coefficient_variation_percent,
                    "p10": series.stats.p10,
                    "p50": series.stats.p50,
                    "p90": series.stats.p90,
                }
            )
        return output.getvalue()


def _samples_to_csv(samples: list[Sample]) -> str:
    output = StringIO()
    fieldnames = [
        "sample_code",
        "well",
        "depth_m",
        "porosity_fraction",
        "permeability_md",
        "rock_type",
        "lithology_micro",
        "vp_m_s",
        "confining_pressure_psi",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for sample in samples:
        writer.writerow(sample.model_dump())
    return output.getvalue()
