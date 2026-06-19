import csv
from functools import lru_cache
from pathlib import Path

from mlmodel.schemas.samples import (
    BasicPetrophysics,
    MineralogyComponent,
    Petrography,
    Sample,
    SampleDetail,
    SonicVelocity,
)


class LocalSampleRepository:
    def list_samples(self) -> list[Sample]:
        return _load_fixture_samples()

    def get_sample_detail(self, sample_code: str) -> SampleDetail | None:
        samples = {sample.sample_code: sample for sample in self.list_samples()}
        sample = samples.get(sample_code)
        if sample is None:
            return None

        return SampleDetail(
            sample=sample,
            basic_petrophysics=_load_basic_petrophysics().get(sample_code),
            petrography=_load_petrography().get(sample_code),
            mineralogy_total=_load_mineralogy("mineralogy_total.csv").get(sample_code, []),
            mineralogy_clays=_load_mineralogy("mineralogy_clays.csv").get(sample_code, []),
            sonic_velocity=_load_sonic_velocity().get(sample_code),
        )


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


def _fixture_file(filename: str) -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "fixtures" / filename


@lru_cache
def _load_basic_petrophysics() -> dict[str, BasicPetrophysics]:
    with _fixture_file("basic_petrophysics.csv").open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return {
            row["sample_code"]: BasicPetrophysics(
                porosity_fraction=float(row["porosity_fraction"]),
                permeability_md=float(row["permeability_md"]),
                grain_density_g_cm3=float(row["grain_density_g_cm3"]),
                pore_volume_cm3=float(row["pore_volume_cm3"]),
                diameter_mm=float(row["diameter_mm"]),
                confining_pressure_psi=float(row["confining_pressure_psi"]),
                fluid=row["fluid"],
                klinkenberg=row["klinkenberg"],
                drying=row["drying"],
                sample_type=row["sample_type"],
            )
            for row in reader
        }


@lru_cache
def _load_petrography() -> dict[str, Petrography]:
    with _fixture_file("petrography.csv").open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return {
            row["sample_code"]: Petrography(
                macro_class=row["macro_class"],
                macro_type=row["macro_type"],
                micro_type=row["micro_type"],
            )
            for row in reader
        }


@lru_cache
def _load_mineralogy(filename: str) -> dict[str, list[MineralogyComponent]]:
    mineralogy: dict[str, list[MineralogyComponent]] = {}
    with _fixture_file(filename).open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            mineralogy.setdefault(row["sample_code"], []).append(
                MineralogyComponent(
                    mineral=row["mineral"],
                    percent=float(row["percent"]),
                )
            )
    return mineralogy


@lru_cache
def _load_sonic_velocity() -> dict[str, SonicVelocity]:
    with _fixture_file("sonic_velocity.csv").open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return {
            row["sample_code"]: SonicVelocity(
                vp_m_s=float(row["vp_m_s"]),
                vs1_m_s=float(row["vs1_m_s"]),
                vs2_m_s=float(row["vs2_m_s"]),
                bulk_density_g_cm3=float(row["bulk_density_g_cm3"]),
                poisson_ratio=float(row["poisson_ratio"]),
                velocity_confining_pressure_psi=float(row["velocity_confining_pressure_psi"]),
                condition=row["condition"],
            )
            for row in reader
        }
