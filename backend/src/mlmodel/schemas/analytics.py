from typing import Literal

from pydantic import BaseModel

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
