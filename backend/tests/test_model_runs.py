import csv
from io import StringIO

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


def test_create_model_run_returns_503_when_mlflow_logging_fails(
    monkeypatch: MonkeyPatch,
) -> None:
    _force_local_repository(monkeypatch)

    def fail_mlflow_logging(settings, model_run):
        raise RuntimeError("MLflow logging requires mlflow.")

    monkeypatch.setattr(
        "mlmodel.api.routes.model_runs.log_model_run_to_mlflow",
        fail_mlflow_logging,
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

    assert response.status_code == 503
    assert response.json()["detail"] == "MLflow logging requires mlflow."


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


def test_run_and_save_softsand_model_run(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs/rockphypy/softsand",
        json={
            "parameters": {
                "mineral_bulk_modulus_gpa": 37.0,
                "mineral_shear_modulus_gpa": 44.0,
                "porosity_fraction": 0.25,
                "critical_porosity_fraction": 0.4,
                "coordination_number": 8.6,
                "effective_stress_mpa": 20.0,
                "reduced_shear_factor": 0.5,
            }
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["model_name"] == "rockphypy.softsand"
    assert payload["engine"] in {"rockphypy", "local-granular-media-fallback"}
    assert payload["parameters"]["porosity_fraction"] == 0.25
    assert payload["result"]["dry_bulk_modulus_gpa"] > 0
    assert "Soft-sand dry-frame model" in payload["assumptions"]


def test_run_and_save_stiffsand_model_run(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs/rockphypy/stiffsand",
        json={
            "parameters": {
                "mineral_bulk_modulus_gpa": 37.0,
                "mineral_shear_modulus_gpa": 44.0,
                "porosity_fraction": 0.25,
                "critical_porosity_fraction": 0.4,
                "coordination_number": 8.6,
                "effective_stress_mpa": 20.0,
                "reduced_shear_factor": 0.5,
            }
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["model_name"] == "rockphypy.stiffsand"
    assert payload["engine"] in {"rockphypy", "local-granular-media-fallback"}
    assert payload["parameters"]["porosity_fraction"] == 0.25
    assert payload["result"]["dry_shear_modulus_gpa"] > 0
    assert "Stiff-sand dry-frame model" in payload["assumptions"]


def test_run_and_save_aki_richards_model_run(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs/rockphypy/avo/aki-richards",
        json={
            "parameters": {
                "incident_angles_degrees": [0, 10, 20],
                "vp_upper_m_s": 3000.0,
                "vp_lower_m_s": 3300.0,
                "vs_upper_m_s": 1500.0,
                "vs_lower_m_s": 1650.0,
                "density_upper_kg_m3": 2300.0,
                "density_lower_kg_m3": 2400.0,
            }
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["model_name"] == "rockphypy.avo.aki_richards"
    assert payload["engine"] in {"rockphypy", "local-avo-fallback"}
    assert payload["parameters"]["incident_angles_degrees"] == [0.0, 10.0, 20.0]
    assert len(payload["result"]["pp_reflectivity"]) == 3
    assert "Aki-Richards PP reflectivity approximation" in payload["assumptions"]


def test_run_and_save_rockphypy_json_batch_model_run(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs/rockphypy/batch",
        json={
            "model": "softsand",
            "rows": [
                {
                    "mineral_bulk_modulus_gpa": 37.0,
                    "mineral_shear_modulus_gpa": 44.0,
                    "porosity_fraction": 0.25,
                    "critical_porosity_fraction": 0.4,
                    "coordination_number": 8.6,
                    "effective_stress_mpa": 20.0,
                    "reduced_shear_factor": 0.5,
                },
                {
                    "mineral_bulk_modulus_gpa": 37.0,
                    "mineral_shear_modulus_gpa": 44.0,
                    "porosity_fraction": 1.2,
                    "critical_porosity_fraction": 0.4,
                    "coordination_number": 8.6,
                    "effective_stress_mpa": 20.0,
                    "reduced_shear_factor": 0.5,
                },
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["model_name"] == "rockphypy.batch.softsand"
    assert payload["parameters"]["input_format"] == "json"
    assert payload["result"]["row_count"] == 2
    assert payload["result"]["successful_count"] == 1
    assert payload["result"]["failed_count"] == 1
    assert payload["result"]["rows"][0]["status"] == "success"
    assert payload["result"]["rows"][1]["status"] == "error"


def test_run_and_save_rockphypy_csv_batch_model_run(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs/rockphypy/batch",
        json={
            "model": "avo.aki-richards",
            "csv_text": (
                "incident_angles_degrees,vp_upper_m_s,vp_lower_m_s,vs_upper_m_s,"
                "vs_lower_m_s,density_upper_kg_m3,density_lower_kg_m3\n"
                "\"0;10;20\",3000,3300,1500,1650,2300,2400\n"
            ),
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["model_name"] == "rockphypy.batch.avo.aki_richards"
    assert payload["parameters"]["input_format"] == "csv"
    assert payload["result"]["row_count"] == 1
    assert payload["result"]["successful_count"] == 1
    assert payload["result"]["rows"][0]["parameters"]["incident_angles_degrees"] == [
        0.0,
        10.0,
        20.0,
    ]
    assert len(payload["result"]["rows"][0]["result"]["pp_reflectivity"]) == 3


def test_run_and_save_rockphypy_batch_rejects_multiple_input_formats(
    monkeypatch: MonkeyPatch,
) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/api/model-runs/rockphypy/batch",
        json={
            "model": "softsand",
            "rows": [{"porosity_fraction": 0.25}],
            "csv_text": "porosity_fraction\n0.25\n",
        },
    )

    assert response.status_code == 422


def test_export_model_run_json_returns_existing_model_run(monkeypatch: MonkeyPatch) -> None:
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

    response = client.get(f"/api/model-runs/{created['run_id']}/export/json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == created["run_id"]
    assert payload["parameters"] == {"x": 1}
    assert payload["result"] == {"y": 2}


def test_export_simple_model_run_csv_returns_flat_row(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    created = client.post(
        "/api/model-runs",
        json={
            "model_name": "custom-model",
            "engine": "test-engine",
            "parameters": {"x": 1},
            "result": {"y": 2},
        },
    ).json()

    response = client.get(f"/api/model-runs/{created['run_id']}/export/csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        f'attachment; filename="model-run-{created["run_id"]}.csv"'
    )
    rows = list(csv.DictReader(StringIO(response.text)))
    assert len(rows) == 1
    assert rows[0]["run_id"] == created["run_id"]
    assert rows[0]["model_name"] == "custom-model"
    assert rows[0]["engine"] == "test-engine"
    assert rows[0]["parameters.x"] == "1"
    assert rows[0]["result.y"] == "2"


def test_export_batch_model_run_csv_returns_success_and_error_rows(
    monkeypatch: MonkeyPatch,
) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    created = client.post(
        "/api/model-runs/rockphypy/batch",
        json={
            "model": "softsand",
            "rows": [
                {
                    "mineral_bulk_modulus_gpa": 37.0,
                    "mineral_shear_modulus_gpa": 44.0,
                    "porosity_fraction": 0.25,
                    "critical_porosity_fraction": 0.4,
                    "coordination_number": 8.6,
                    "effective_stress_mpa": 20.0,
                    "reduced_shear_factor": 0.5,
                },
                {
                    "mineral_bulk_modulus_gpa": 37.0,
                    "mineral_shear_modulus_gpa": 44.0,
                    "porosity_fraction": 1.2,
                    "critical_porosity_fraction": 0.4,
                    "coordination_number": 8.6,
                    "effective_stress_mpa": 20.0,
                    "reduced_shear_factor": 0.5,
                },
            ],
        },
    ).json()

    response = client.get(f"/api/model-runs/{created['run_id']}/export/csv")

    assert response.status_code == 200
    rows = list(csv.DictReader(StringIO(response.text)))
    assert len(rows) == 2
    assert rows[0]["status"] == "success"
    assert rows[0]["batch_model"] == "softsand"
    assert rows[0]["parameters.porosity_fraction"] == "0.25"
    assert float(rows[0]["result.dry_bulk_modulus_gpa"]) > 0
    assert rows[1]["status"] == "error"
    assert rows[1]["parameters.porosity_fraction"] == "1.2"
    assert "porosity_fraction" in rows[1]["error"]


def test_export_model_run_returns_404_for_unknown_id(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/api/model-runs/unknown-run/export/csv")

    assert response.status_code == 404
    assert response.json()["detail"] == "Model run 'unknown-run' was not found."


def test_get_model_run_returns_404_for_unknown_id(monkeypatch: MonkeyPatch) -> None:
    _force_local_repository(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/api/model-runs/unknown-run")

    assert response.status_code == 404
    assert response.json()["detail"] == "Model run 'unknown-run' was not found."
