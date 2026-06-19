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
