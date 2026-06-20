from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from mlmodel.core.config import get_settings
from mlmodel.main import create_app


def _force_local_repository(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MLMODEL_ANALYSIS_REPOSITORY_BACKEND", "local")
    monkeypatch.delenv("MLMODEL_MLFLOW_TRACKING_URI", raising=False)
    get_settings.cache_clear()


def test_create_model_run(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs",
        json={
            "model_name": "rockphypy.gassmann",
            "model_version": "0.1.0",
            "engine": "local-gassmann-fallback",
            "parameters": {"porosity_fraction": 0.2},
            "result": {"vp_m_s": 4659.0},
            "assumptions": ["Gassmann low-frequency fluid substitution"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["run_id"]
    assert payload["model_name"] == "rockphypy.gassmann"
    assert payload["parameters"]["porosity_fraction"] == 0.2
    assert payload["result"]["vp_m_s"] == 4659.0
    assert payload["saved_analysis_id"] is None
    assert payload["mlflow_run_id"] is None


def test_create_model_run_persists_mlflow_run_id_when_logged(
    monkeypatch: MonkeyPatch,
) -> None:
    _force_local_repository(monkeypatch)
    monkeypatch.setattr(
        "mlmodel.api.routes.model_runs.log_model_run_to_mlflow",
        lambda settings, model_run: "mlflow-run-123",
    )
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs",
        json={
            "model_name": "rockphypy.gassmann",
            "parameters": {"porosity_fraction": 0.2},
            "result": {"vp_m_s": 4659.0},
        },
    )

    assert response.status_code == 201
    assert response.json()["mlflow_run_id"] == "mlflow-run-123"


def test_get_model_run_by_id(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    created = client.post(
        "/api/model-runs",
        json={
            "model_name": "custom-model",
            "parameters": {"x": 1},
            "result": {"y": 2},
        },
    ).json()

    response = client.get(f"/api/model-runs/{created['run_id']}")

    assert response.status_code == 200
    assert response.json()["run_id"] == created["run_id"]


def test_model_runs_can_be_filtered_by_saved_analysis(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    analysis = client.post(
        "/api/analyses",
        json={
            "title": "Model comparison",
            "analysis_type": "rock_physics",
            "configuration": {},
        },
    ).json()

    client.post(
        "/api/model-runs",
        json={
            "model_name": "linked-model",
            "parameters": {"x": 1},
            "result": {"y": 2},
            "saved_analysis_id": analysis["analysis_id"],
        },
    )
    client.post(
        "/api/model-runs",
        json={
            "model_name": "unlinked-model",
            "parameters": {"x": 3},
            "result": {"y": 4},
        },
    )

    response = client.get(f"/api/analyses/{analysis['analysis_id']}/model-runs")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["model_name"] == "linked-model"
    assert payload[0]["saved_analysis_id"] == analysis["analysis_id"]


def test_run_and_save_gassmann_model_run(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs/rockphypy/gassmann",
        json={
            "parameters": {
                "mineral_bulk_modulus_gpa": 37.0,
                "mineral_shear_modulus_gpa": 44.0,
                "mineral_density_g_cm3": 2.65,
                "fluid_bulk_modulus_gpa": 2.2,
                "fluid_density_g_cm3": 1.0,
                "porosity_fraction": 0.2,
                "critical_porosity_fraction": 0.4,
            }
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["model_name"] == "rockphypy.gassmann"
    assert payload["engine"] in {"rockphypy", "local-gassmann-fallback"}
    assert payload["parameters"]["porosity_fraction"] == 0.2
    assert round(payload["result"]["vp_m_s"], 1) == 4659.0
    assert "Gassmann low-frequency fluid substitution" in payload["assumptions"]


def test_get_model_run_returns_404_for_unknown_id(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/api/model-runs/unknown-run")

    assert response.status_code == 404
    assert response.json()["detail"] == "Model run 'unknown-run' was not found."
