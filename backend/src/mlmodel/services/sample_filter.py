from mlmodel.schemas.filters import SampleFilters
from mlmodel.schemas.samples import Sample


def filter_samples(samples: list[Sample], filters: SampleFilters | None) -> list[Sample]:
    if filters is None:
        return samples

    return [sample for sample in samples if _matches(sample, filters)]


def _matches(sample: Sample, filters: SampleFilters) -> bool:
    porosity_percent = sample.porosity_fraction * 100

    return (
        _in_optional(sample.sample_code, filters.sample_codes)
        and _in_optional(sample.well, filters.wells)
        and _in_optional(sample.rock_type, filters.rock_types)
        and _in_optional(sample.lithology_micro, filters.lithologies)
        and _gte_optional(sample.depth_m, filters.min_depth_m)
        and _lte_optional(sample.depth_m, filters.max_depth_m)
        and _gte_optional(porosity_percent, filters.min_porosity_percent)
        and _lte_optional(porosity_percent, filters.max_porosity_percent)
        and _gte_optional(sample.confining_pressure_psi, filters.min_confining_pressure_psi)
        and _lte_optional(sample.confining_pressure_psi, filters.max_confining_pressure_psi)
    )


def _in_optional(value: str, allowed_values: list[str] | None) -> bool:
    return not allowed_values or value in allowed_values


def _gte_optional(value: float, minimum: float | None) -> bool:
    return minimum is None or value >= minimum


def _lte_optional(value: float, maximum: float | None) -> bool:
    return maximum is None or value <= maximum
