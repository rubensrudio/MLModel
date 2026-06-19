from fastapi.testclient import TestClient

from mlmodel.main import create_app


def test_list_samples_returns_fixture_samples() -> None:
    client = TestClient(create_app())

    response = client.get("/api/samples")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 6
    assert payload[0]["sample_code"] == "F244V"
    assert payload[0]["porosity_fraction"] == 0.192


def test_samples_summary_returns_dashboard_kpis() -> None:
    client = TestClient(create_app())

    response = client.get("/api/samples/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 6
    assert payload["well_count"] == 4
    assert payload["rock_type_count"] == 5
    assert payload["min_depth_m"] == 4858.0
    assert payload["max_depth_m"] == 5079.5
    assert round(payload["average_porosity_percent"], 2) == 21.22
    assert round(payload["average_vp_m_s"], 2) == 4695.33
