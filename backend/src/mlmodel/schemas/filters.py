from pydantic import BaseModel, Field, model_validator


class SampleFilters(BaseModel):
    sample_codes: list[str] | None = None
    wells: list[str] | None = None
    rock_types: list[str] | None = None
    lithologies: list[str] | None = None
    min_depth_m: float | None = Field(default=None, ge=0)
    max_depth_m: float | None = Field(default=None, ge=0)
    min_porosity_percent: float | None = Field(default=None, ge=0, le=100)
    max_porosity_percent: float | None = Field(default=None, ge=0, le=100)
    min_confining_pressure_psi: float | None = Field(default=None, ge=0)
    max_confining_pressure_psi: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_ranges(self) -> "SampleFilters":
        _validate_range(self.min_depth_m, self.max_depth_m, "depth")
        _validate_range(self.min_porosity_percent, self.max_porosity_percent, "porosity")
        _validate_range(
            self.min_confining_pressure_psi,
            self.max_confining_pressure_psi,
            "confining pressure",
        )
        return self


def _validate_range(min_value: float | None, max_value: float | None, label: str) -> None:
    if min_value is not None and max_value is not None and min_value > max_value:
        raise ValueError(f"Minimum {label} cannot be greater than maximum {label}.")
