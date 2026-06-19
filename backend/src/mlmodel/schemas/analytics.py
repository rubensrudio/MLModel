from typing import Literal

from pydantic import BaseModel, Field

from mlmodel.schemas.filters import SampleFilters

NumericSampleField = Literal[
    "depth_m",
    "porosity_percent",
    "permeability_md",
    "vp_m_s",
    "confining_pressure_psi",
]

CategorySampleField = Literal[
    "well",
    "rock_type",
    "lithology_micro",
]


class CrossplotRequest(BaseModel):
    x_field: NumericSampleField
    y_field: NumericSampleField
    color_by: CategorySampleField | None = None
    filters: SampleFilters | None = None


class CrossplotPoint(BaseModel):
    sample_code: str
    x: float
    y: float
    color: str | None = None


class CrossplotResponse(BaseModel):
    x_field: NumericSampleField
    y_field: NumericSampleField
    color_by: CategorySampleField | None
    points: list[CrossplotPoint]


class AnalyticsStats(BaseModel):
    count: int = Field(ge=0)
    mean: float
    median: float
    standard_deviation: float
    coefficient_variation_percent: float | None
    minimum: float
    maximum: float
    p10: float
    p50: float
    p90: float


class HistogramRequest(BaseModel):
    field: NumericSampleField
    bins: int = Field(default=10, ge=1, le=100)
    group_by: CategorySampleField | None = None
    filters: SampleFilters | None = None


class HistogramBin(BaseModel):
    start: float
    end: float
    count: int = Field(ge=0)


class HistogramSeries(BaseModel):
    group: str | None
    bins: list[HistogramBin]
    sample_count: int = Field(ge=0)
    stats: AnalyticsStats


class HistogramResponse(BaseModel):
    field: NumericSampleField
    group_by: CategorySampleField | None
    bins: list[HistogramBin]
    sample_count: int = Field(ge=0)
    stats: AnalyticsStats | None
    series: list[HistogramSeries]


class BoxplotRequest(BaseModel):
    field: NumericSampleField
    group_by: CategorySampleField | None = None
    filters: SampleFilters | None = None


class BoxplotSeries(BaseModel):
    group: str | None
    count: int = Field(ge=0)
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float
    mean: float
    stats: AnalyticsStats


class BoxplotResponse(BaseModel):
    field: NumericSampleField
    group_by: CategorySampleField | None
    series: list[BoxplotSeries]
