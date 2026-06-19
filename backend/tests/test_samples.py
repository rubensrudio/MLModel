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


def test_list_samples_can_filter_by_well_and_rock_type() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/samples",
        params={
            "wells": "1-RJS-628",
            "rock_types": "Floatstone",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [sample["sample_code"] for sample in payload] == ["G2441V"]


def test_list_samples_accepts_comma_separated_filters() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/samples",
        params={
            "sample_codes": "F244V,G2441V",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [sample["sample_code"] for sample in payload] == ["F244V", "G2441V"]


def test_list_samples_can_filter_by_numeric_ranges() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/samples",
        params={
            "min_porosity_percent": 23,
            "max_depth_m": 5050,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [sample["sample_code"] for sample in payload] == ["F2416V", "G2413V", "H2450V"]


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


def test_samples_summary_uses_filters() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/samples/summary",
        params={
            "wells": "1-RJS-628",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 2
    assert payload["well_count"] == 1
    assert round(payload["average_porosity_percent"], 2) == 19.55


def test_get_sample_detail_returns_expanded_sections() -> None:
    client = TestClient(create_app())

    response = client.get("/api/samples/G2441V")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample"]["sample_code"] == "G2441V"
    assert payload["sample"]["well"] == "1-RJS-628"

    assert payload["basic_petrophysics"]["porosity_fraction"] == 0.199
    assert payload["basic_petrophysics"]["permeability_md"] == 674.0
    assert payload["petrography"] == {
        "macro_class": "Carbonatica",
        "macro_type": "Floatstone",
        "micro_type": "COQUINA FRAGMENTADA",
    }

    total_minerals = {item["mineral"]: item["percent"] for item in payload["mineralogy_total"]}
    assert total_minerals["Calcita"] == 50.0
    assert total_minerals["Dolomita"] == 32.0

    clay_minerals = {item["mineral"]: item["percent"] for item in payload["mineralogy_clays"]}
    assert clay_minerals["Mica"] == 20.0
    assert clay_minerals["Illita-Esmectita Ord."] == 80.0

    assert payload["sonic_velocity"]["vp_m_s"] == 4291.0
    assert payload["sonic_velocity"]["vs1_m_s"] == 2334.0
    assert payload["sonic_velocity"]["condition"] == "A SECO"


def test_get_sample_detail_returns_404_for_unknown_sample() -> None:
    client = TestClient(create_app())

    response = client.get("/api/samples/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sample 'UNKNOWN' was not found."


def test_samples_summary_route_is_not_captured_as_sample_code() -> None:
    client = TestClient(create_app())

    response = client.get("/api/samples/summary")

    assert response.status_code == 200
    assert response.json()["sample_count"] == 6
