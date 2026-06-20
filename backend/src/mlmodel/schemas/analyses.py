from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from mlmodel.schemas.analytics import CategorySampleField, NumericSampleField
from mlmodel.schemas.filters import SampleFilters

AnalysisType = Literal["crossplot", "histogram", "boxplot", "rock_physics"]


class AnalysisComment(BaseModel):
    author: str | None = None
    text: str = Field(min_length=1)


class AnalysisConfiguration(BaseModel):
    x_field: NumericSampleField | None = None
    y_field: NumericSampleField | None = None
    field: NumericSampleField | None = None
    group_by: CategorySampleField | None = None
    color_by: CategorySampleField | None = None
    filters: SampleFilters | None = None


class SavedAnalysisCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    analysis_type: AnalysisType
    configuration: AnalysisConfiguration
    comments: list[AnalysisComment] = Field(default_factory=list)
    selected_models: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None


class SavedAnalysis(SavedAnalysisCreate):
    analysis_id: str
    created_at: datetime
    updated_at: datetime
