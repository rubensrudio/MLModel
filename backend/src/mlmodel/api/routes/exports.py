from fastapi import APIRouter, Depends
from fastapi.responses import Response

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
from mlmodel.schemas.exports import SamplesExportRequest, SamplesJsonExportResponse
from mlmodel.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])


def get_export_service() -> ExportService:
    repository: SampleRepository = LocalSampleRepository()
    return ExportService(repository)


@router.post("/samples/json", response_model=SamplesJsonExportResponse)
def export_samples_json(
    request: SamplesExportRequest,
    service: ExportService = Depends(get_export_service),
) -> SamplesJsonExportResponse:
    return service.export_samples_json(request)


@router.post("/samples/csv")
def export_samples_csv(
    request: SamplesExportRequest,
    service: ExportService = Depends(get_export_service),
) -> Response:
    csv_payload = service.export_samples_csv(request)
    return Response(
        content=csv_payload,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="samples.csv"'},
    )


@router.post("/analytics/crossplot/json", response_model=CrossplotResponse)
def export_crossplot_json(
    request: CrossplotRequest,
    service: ExportService = Depends(get_export_service),
) -> CrossplotResponse:
    return service.export_crossplot_json(request)


@router.post("/analytics/crossplot/csv")
def export_crossplot_csv(
    request: CrossplotRequest,
    service: ExportService = Depends(get_export_service),
) -> Response:
    return _csv_response(service.export_crossplot_csv(request), "crossplot.csv")


@router.post("/analytics/histogram/json", response_model=HistogramResponse)
def export_histogram_json(
    request: HistogramRequest,
    service: ExportService = Depends(get_export_service),
) -> HistogramResponse:
    return service.export_histogram_json(request)


@router.post("/analytics/histogram/csv")
def export_histogram_csv(
    request: HistogramRequest,
    service: ExportService = Depends(get_export_service),
) -> Response:
    return _csv_response(service.export_histogram_csv(request), "histogram.csv")


@router.post("/analytics/boxplot/json", response_model=BoxplotResponse)
def export_boxplot_json(
    request: BoxplotRequest,
    service: ExportService = Depends(get_export_service),
) -> BoxplotResponse:
    return service.export_boxplot_json(request)


@router.post("/analytics/boxplot/csv")
def export_boxplot_csv(
    request: BoxplotRequest,
    service: ExportService = Depends(get_export_service),
) -> Response:
    return _csv_response(service.export_boxplot_csv(request), "boxplot.csv")


def _csv_response(csv_payload: str, filename: str) -> Response:
    return Response(
        content=csv_payload,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
