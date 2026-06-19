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


class BasicPetrophysics(BaseModel):
    porosity_fraction: float = Field(ge=0, le=1)
    permeability_md: float = Field(ge=0)
    grain_density_g_cm3: float = Field(gt=0)
    pore_volume_cm3: float = Field(ge=0)
    diameter_mm: float = Field(gt=0)
    confining_pressure_psi: float = Field(ge=0)
    fluid: str
    klinkenberg: str
    drying: str
    sample_type: str


class Petrography(BaseModel):
    macro_class: str
    macro_type: str
    micro_type: str


class MineralogyComponent(BaseModel):
    mineral: str
    percent: float = Field(ge=0, le=100)


class SonicVelocity(BaseModel):
    vp_m_s: float = Field(gt=0)
    vs1_m_s: float = Field(gt=0)
    vs2_m_s: float = Field(gt=0)
    bulk_density_g_cm3: float = Field(gt=0)
    poisson_ratio: float
    velocity_confining_pressure_psi: float = Field(ge=0)
    condition: str


class SampleDetail(BaseModel):
    sample: Sample
    basic_petrophysics: BasicPetrophysics | None
    petrography: Petrography | None
    mineralogy_total: list[MineralogyComponent]
    mineralogy_clays: list[MineralogyComponent]
    sonic_velocity: SonicVelocity | None
