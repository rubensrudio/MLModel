from fastapi.testclient import TestClient

from mlmodel.main import create_app


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
