from fastapi.testclient import TestClient

from mlmodel.integrations.rockphypy_compat import _nudge_duplicate_color_positions
from mlmodel.main import create_app


def test_rockphypy_legacy_colormap_positions_are_made_strictly_increasing() -> None:
    adjusted = _nudge_duplicate_color_positions(
        [
            (0, "blue"),
            (0.05, "#0a75ad"),
            (0.05, "#4ca3dd"),
            (0.1, "#20b2aa"),
            (1, "red"),
        ]
    )

    assert adjusted is not None
    positions = [position for position, _color in adjusted]
    assert positions == sorted(positions)
    assert len(set(positions)) == len(positions)
    assert positions[2] > 0.05
    assert positions[-1] == 1.0


def test_gassmann_endpoint_returns_physical_response() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/models/rockphypy/gassmann/run",
        json={
            "mineral_bulk_modulus_gpa": 37.0,
            "mineral_shear_modulus_gpa": 44.0,
            "mineral_density_g_cm3": 2.65,
            "fluid_bulk_modulus_gpa": 2.2,
            "fluid_density_g_cm3": 1.0,
            "porosity_fraction": 0.2,
            "critical_porosity_fraction": 0.4,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] in {"rockphypy", "local-gassmann-fallback"}
    assert payload["dry_bulk_modulus_gpa"] == 18.5
    assert payload["dry_shear_modulus_gpa"] == 22.0
    assert round(payload["saturated_bulk_modulus_gpa"], 3) == 21.025
    assert payload["saturated_shear_modulus_gpa"] == 22.0
    assert round(payload["bulk_density_g_cm3"], 2) == 2.32
    assert round(payload["vp_m_s"], 1) == 4659.0
    assert round(payload["vs_m_s"], 1) == 3079.4
    assert round(payload["vp_vs_ratio"], 3) == 1.513


def test_gassmann_endpoint_rejects_invalid_porosity() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/models/rockphypy/gassmann/run",
        json={
            "mineral_bulk_modulus_gpa": 37.0,
            "mineral_shear_modulus_gpa": 44.0,
            "mineral_density_g_cm3": 2.65,
            "fluid_bulk_modulus_gpa": 2.2,
            "fluid_density_g_cm3": 1.0,
            "porosity_fraction": 1.2,
            "critical_porosity_fraction": 0.4,
        },
    )

    assert response.status_code == 422


def test_softsand_endpoint_returns_dry_frame_moduli() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/models/rockphypy/softsand/run",
        json={
            "mineral_bulk_modulus_gpa": 37.0,
            "mineral_shear_modulus_gpa": 44.0,
            "porosity_fraction": 0.25,
            "critical_porosity_fraction": 0.4,
            "coordination_number": 8.6,
            "effective_stress_mpa": 20.0,
            "reduced_shear_factor": 0.5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] in {"rockphypy", "local-granular-media-fallback"}
    assert payload["dry_bulk_modulus_gpa"] > 0
    assert payload["dry_shear_modulus_gpa"] > 0
    assert "Soft-sand dry-frame model" in payload["assumptions"]


def test_stiffsand_endpoint_returns_dry_frame_moduli() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/models/rockphypy/stiffsand/run",
        json={
            "mineral_bulk_modulus_gpa": 37.0,
            "mineral_shear_modulus_gpa": 44.0,
            "porosity_fraction": 0.25,
            "critical_porosity_fraction": 0.4,
            "coordination_number": 8.6,
            "effective_stress_mpa": 20.0,
            "reduced_shear_factor": 0.5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] in {"rockphypy", "local-granular-media-fallback"}
    assert payload["dry_bulk_modulus_gpa"] > 0
    assert payload["dry_shear_modulus_gpa"] > 0
    assert "Stiff-sand dry-frame model" in payload["assumptions"]


def test_aki_richards_endpoint_returns_angle_series() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/models/rockphypy/avo/aki-richards/run",
        json={
            "incident_angles_degrees": [0, 10, 20, 30],
            "vp_upper_m_s": 3000.0,
            "vp_lower_m_s": 3300.0,
            "vs_upper_m_s": 1500.0,
            "vs_lower_m_s": 1650.0,
            "density_upper_kg_m3": 2300.0,
            "density_lower_kg_m3": 2400.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] in {"rockphypy", "local-avo-fallback"}
    assert len(payload["pp_reflectivity"]) == 4
    assert len(payload["ps_reflectivity"]) == 4
    assert round(payload["pp_reflectivity"][0], 6) == round(payload["intercept"], 6)
    assert "Aki-Richards PP reflectivity approximation" in payload["assumptions"]


def test_aki_richards_endpoint_rejects_empty_angles() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/models/rockphypy/avo/aki-richards/run",
        json={
            "incident_angles_degrees": [],
            "vp_upper_m_s": 3000.0,
            "vp_lower_m_s": 3300.0,
            "vs_upper_m_s": 1500.0,
            "vs_lower_m_s": 1650.0,
            "density_upper_kg_m3": 2300.0,
            "density_lower_kg_m3": 2400.0,
        },
    )

    assert response.status_code == 422
