from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from mlmodel.core.config import get_settings
from mlmodel.main import create_app


def _force_local_repository(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MLMODEL_ANALYSIS_REPOSITORY_BACKEND", "local")
    get_settings.cache_clear()


def test_create_saved_crossplot_analysis(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/analyses",
        json={
            "title": "Porosity vs Vp review",
            "analysis_type": "crossplot",
            "configuration": {
                "x_field": "porosity_percent",
                "y_field": "vp_m_s",
                "color_by": "rock_type",
                "filters": {
                    "wells": ["1-RJS-628"],
                    "rock_types": ["Floatstone"],
                },
            },
            "comments": [
                {
                    "author": "petrophysics",
                    "text": "Review high-porosity samples.",
                }
            ],
            "selected_models": ["gassmann-critical-porosity"],
            "result": {
                "indicators": {
                    "sample_count": 1,
                    "pearson_correlation": None,
                    "mean_absolute_error": None,
                }
            },
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["analysis_id"]
    assert payload["title"] == "Porosity vs Vp review"
    assert payload["analysis_type"] == "crossplot"
    assert payload["configuration"]["x_field"] == "porosity_percent"
    assert payload["configuration"]["filters"]["wells"] == ["1-RJS-628"]
    assert payload["comments"][0]["text"] == "Review high-porosity samples."
    assert payload["selected_models"] == ["gassmann-critical-porosity"]
    assert payload["result"]["indicators"]["sample_count"] == 1
    assert payload["created_at"] == payload["updated_at"]


def test_list_saved_analyses_includes_created_analysis(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    created = client.post(
        "/api/analyses",
        json={
            "title": "Histogram saved analysis",
            "analysis_type": "histogram",
            "configuration": {
                "field": "porosity_percent",
                "group_by": "rock_type",
            },
        },
    ).json()

    response = client.get("/api/analyses")

    assert response.status_code == 200
    payload = response.json()
    assert any(analysis["analysis_id"] == created["analysis_id"] for analysis in payload)


def test_get_saved_analysis_by_id(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    created = client.post(
        "/api/analyses",
        json={
            "title": "Boxplot saved analysis",
            "analysis_type": "boxplot",
            "configuration": {
                "field": "vp_m_s",
                "group_by": "well",
            },
        },
    ).json()

    response = client.get(f"/api/analyses/{created['analysis_id']}")

    assert response.status_code == 200
    assert response.json()["analysis_id"] == created["analysis_id"]


def test_get_saved_analysis_returns_404_for_unknown_id(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/api/analyses/unknown-analysis")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis 'unknown-analysis' was not found."


def test_create_saved_analysis_rejects_invalid_field(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/analyses",
        json={
            "title": "Invalid analysis",
            "analysis_type": "crossplot",
            "configuration": {
                "x_field": "not_a_field",
                "y_field": "vp_m_s",
            },
        },
    )

    assert response.status_code == 422
