from statistics import fmean, pstdev

from mlmodel.repositories.sample_repository import SampleRepository
from mlmodel.schemas.analytics import (
    AnalyticsStats,
    BoxplotRequest,
    BoxplotResponse,
    BoxplotSeries,
    CrossplotComparisonPoint,
    CrossplotComparisonRequest,
    CrossplotComparisonResponse,
    CrossplotIndicators,
    CrossplotPoint,
    CrossplotRequest,
    CrossplotResponse,
    HistogramBin,
    HistogramRequest,
    HistogramResponse,
    HistogramSeries,
)
from mlmodel.schemas.samples import Sample
from mlmodel.services.sample_filter import filter_samples


class AnalyticsService:
    def __init__(self, repository: SampleRepository) -> None:
        self._repository = repository

    def create_crossplot(self, request: CrossplotRequest) -> CrossplotResponse:
        samples = filter_samples(self._repository.list_samples(), request.filters)
        points = [
            CrossplotPoint(
                sample_code=sample.sample_code,
                x=_numeric_value(sample, request.x_field),
                y=_numeric_value(sample, request.y_field),
                color=_category_value(sample, request.color_by) if request.color_by else None,
            )
            for sample in samples
        ]
        return CrossplotResponse(
            x_field=request.x_field,
            y_field=request.y_field,
            color_by=request.color_by,
            points=points,
            indicators=_crossplot_indicators(points),
        )

    def compare_crossplot(self, request: CrossplotComparisonRequest) -> CrossplotComparisonResponse:
        samples = filter_samples(self._repository.list_samples(), request.filters)
        predictions_by_sample = {
            prediction.sample_code: prediction.predicted_y
            for prediction in request.predictions
        }
        points = [
            _comparison_point(sample, request, predictions_by_sample[sample.sample_code])
            for sample in samples
            if sample.sample_code in predictions_by_sample
        ]
        return CrossplotComparisonResponse(
            x_field=request.x_field,
            y_field=request.y_field,
            color_by=request.color_by,
            points=points,
            indicators=_crossplot_indicators(points),
        )

    def create_histogram(self, request: HistogramRequest) -> HistogramResponse:
        samples = filter_samples(self._repository.list_samples(), request.filters)
        values = [_numeric_value(sample, request.field) for sample in samples]
        if not values:
            return HistogramResponse(
                field=request.field,
                group_by=request.group_by,
                bins=[],
                sample_count=0,
                stats=None,
                series=[],
            )

        grouped_values: dict[str | None, list[float]] = {}
        if request.group_by:
            for sample in samples:
                group = _category_value(sample, request.group_by)
                grouped_values.setdefault(group, []).append(_numeric_value(sample, request.field))

        aggregate_bins = _histogram_bins(values, request.bins)
        series = [
            HistogramSeries(
                group=group,
                bins=_histogram_bins(group_values, request.bins),
                sample_count=len(group_values),
                stats=_stats(group_values),
            )
            for group, group_values in sorted(
                grouped_values.items(),
                key=lambda item: item[0] or "",
            )
        ]
        return HistogramResponse(
            field=request.field,
            group_by=request.group_by,
            bins=aggregate_bins,
            sample_count=len(values),
            stats=_stats(values),
            series=series,
        )

    def create_boxplot(self, request: BoxplotRequest) -> BoxplotResponse:
        samples = filter_samples(self._repository.list_samples(), request.filters)
        grouped_values: dict[str | None, list[float]] = {}

        for sample in samples:
            group = _category_value(sample, request.group_by) if request.group_by else None
            grouped_values.setdefault(group, []).append(_numeric_value(sample, request.field))

        return BoxplotResponse(
            field=request.field,
            group_by=request.group_by,
            series=[
                _boxplot_series(group, values)
                for group, values in sorted(grouped_values.items(), key=lambda item: item[0] or "")
            ],
        )


def _numeric_value(sample: Sample, field: str) -> float:
    if field == "porosity_percent":
        return sample.porosity_fraction * 100
    return float(getattr(sample, field))


def _category_value(sample: Sample, field: str) -> str:
    return str(getattr(sample, field))


def _comparison_point(
    sample: Sample,
    request: CrossplotComparisonRequest,
    predicted_y: float,
) -> CrossplotComparisonPoint:
    actual_y = _numeric_value(sample, request.y_field)
    return CrossplotComparisonPoint(
        sample_code=sample.sample_code,
        x=_numeric_value(sample, request.x_field),
        y=actual_y,
        color=_category_value(sample, request.color_by) if request.color_by else None,
        predicted_y=predicted_y,
        absolute_error=abs(actual_y - predicted_y),
    )


def _crossplot_indicators(
    points: list[CrossplotPoint] | list[CrossplotComparisonPoint],
) -> CrossplotIndicators:
    absolute_errors = [
        point.absolute_error
        for point in points
        if isinstance(point, CrossplotComparisonPoint)
    ]
    return CrossplotIndicators(
        sample_count=len(points),
        pearson_correlation=_pearson_correlation(
            [point.x for point in points],
            [point.y for point in points],
        ),
        mean_absolute_error=fmean(absolute_errors) if absolute_errors else None,
    )


def _pearson_correlation(x_values: list[float], y_values: list[float]) -> float | None:
    if len(x_values) < 2:
        return None

    x_mean = fmean(x_values)
    y_mean = fmean(y_values)
    x_deltas = [value - x_mean for value in x_values]
    y_deltas = [value - y_mean for value in y_values]
    x_sum_squares = sum(delta**2 for delta in x_deltas)
    y_sum_squares = sum(delta**2 for delta in y_deltas)

    if x_sum_squares == 0 or y_sum_squares == 0:
        return None

    covariance = sum(
        x_delta * y_delta for x_delta, y_delta in zip(x_deltas, y_deltas, strict=True)
    )
    return covariance / (x_sum_squares * y_sum_squares) ** 0.5


def _boxplot_series(group: str | None, values: list[float]) -> BoxplotSeries:
    sorted_values = sorted(values)
    return BoxplotSeries(
        group=group,
        count=len(sorted_values),
        minimum=sorted_values[0],
        q1=_percentile(sorted_values, 0.25),
        median=_percentile(sorted_values, 0.50),
        q3=_percentile(sorted_values, 0.75),
        maximum=sorted_values[-1],
        mean=fmean(sorted_values),
        stats=_stats(sorted_values),
    )


def _percentile(sorted_values: list[float], fraction: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (len(sorted_values) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = position - lower_index
    return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight


def _histogram_bins(values: list[float], bin_count: int) -> list[HistogramBin]:
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        return [HistogramBin(start=min_value, end=max_value, count=len(values))]

    width = (max_value - min_value) / bin_count
    bins = [
        HistogramBin(
            start=min_value + index * width,
            end=min_value + (index + 1) * width,
            count=0,
        )
        for index in range(bin_count)
    ]

    counts = [0 for _ in bins]
    for value in values:
        index = int((value - min_value) / width)
        if index == bin_count:
            index -= 1
        counts[index] += 1

    return [
        HistogramBin(start=bin_.start, end=bin_.end, count=count)
        for bin_, count in zip(bins, counts, strict=True)
    ]


def _stats(values: list[float]) -> AnalyticsStats:
    sorted_values = sorted(values)
    mean = fmean(sorted_values)
    standard_deviation = pstdev(sorted_values)
    coefficient_variation = None if mean == 0 else standard_deviation / mean * 100

    return AnalyticsStats(
        count=len(sorted_values),
        mean=mean,
        median=_percentile(sorted_values, 0.5),
        standard_deviation=standard_deviation,
        coefficient_variation_percent=coefficient_variation,
        minimum=sorted_values[0],
        maximum=sorted_values[-1],
        p10=_percentile(sorted_values, 0.1),
        p50=_percentile(sorted_values, 0.5),
        p90=_percentile(sorted_values, 0.9),
    )
