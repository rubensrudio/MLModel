from pydantic import BaseModel, Field


class GassmannRequest(BaseModel):
    mineral_bulk_modulus_gpa: float = Field(gt=0)
    mineral_shear_modulus_gpa: float = Field(gt=0)
    mineral_density_g_cm3: float = Field(gt=0)
    fluid_bulk_modulus_gpa: float = Field(gt=0)
    fluid_density_g_cm3: float = Field(gt=0)
    porosity_fraction: float = Field(ge=0, lt=1)
    critical_porosity_fraction: float = Field(gt=0, le=1)


class GassmannResponse(BaseModel):
    dry_bulk_modulus_gpa: float
    dry_shear_modulus_gpa: float
    saturated_bulk_modulus_gpa: float
    saturated_shear_modulus_gpa: float
    bulk_density_g_cm3: float
    vp_m_s: float
    vs_m_s: float
    acoustic_impedance: float
    vp_vs_ratio: float
    engine: str
    assumptions: list[str]


class GranularMediaRequest(BaseModel):
    mineral_bulk_modulus_gpa: float = Field(gt=0)
    mineral_shear_modulus_gpa: float = Field(gt=0)
    porosity_fraction: float = Field(ge=0, lt=1)
    critical_porosity_fraction: float = Field(gt=0, le=1)
    coordination_number: float = Field(gt=0)
    effective_stress_mpa: float = Field(gt=0)
    reduced_shear_factor: float = Field(ge=0, le=1)


class GranularMediaResponse(BaseModel):
    dry_bulk_modulus_gpa: float
    dry_shear_modulus_gpa: float
    engine: str
    assumptions: list[str]


class AkiRichardsRequest(BaseModel):
    incident_angles_degrees: list[float] = Field(min_length=1)
    vp_upper_m_s: float = Field(gt=0)
    vp_lower_m_s: float = Field(gt=0)
    vs_upper_m_s: float = Field(gt=0)
    vs_lower_m_s: float = Field(gt=0)
    density_upper_kg_m3: float = Field(gt=0)
    density_lower_kg_m3: float = Field(gt=0)


class AkiRichardsResponse(BaseModel):
    pp_reflectivity: list[float]
    ps_reflectivity: list[float]
    intercept: float
    gradient: float
    engine: str
    assumptions: list[str]
