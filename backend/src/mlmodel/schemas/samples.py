from pydantic import BaseModel, Field


class Sample(BaseModel):
    sample_code: str
    well: str
    depth_m: float = Field(ge=0)
    porosity_fraction: float = Field(ge=0, le=1)
    permeability_md: float = Field(ge=0)
    rock_type: str
    lithology_micro: str
    vp_m_s: float = Field(gt=0)
    confining_pressure_psi: float = Field(ge=0)


class SamplesSummary(BaseModel):
    sample_count: int = Field(ge=0)
    well_count: int = Field(ge=0)
    rock_type_count: int = Field(ge=0)
    min_depth_m: float | None
    max_depth_m: float | None
    average_porosity_percent: float | None
    average_vp_m_s: float | None
