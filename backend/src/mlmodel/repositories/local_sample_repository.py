import csv
from functools import lru_cache
from pathlib import Path

from mlmodel.schemas.samples import Sample


class LocalSampleRepository:
    def list_samples(self) -> list[Sample]:
        return _load_fixture_samples()


@lru_cache
def _load_fixture_samples() -> list[Sample]:
    fixture_path = _fixture_path()
    with fixture_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            Sample(
                sample_code=row["sample_code"],
                well=row["well"],
                depth_m=float(row["depth_m"]),
                porosity_fraction=float(row["porosity_fraction"]),
                permeability_md=float(row["permeability_md"]),
                rock_type=row["rock_type"],
                lithology_micro=row["lithology_micro"],
                vp_m_s=float(row["vp_m_s"]),
                confining_pressure_psi=float(row["confining_pressure_psi"]),
            )
            for row in reader
        ]


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "fixtures" / "samples.csv"
