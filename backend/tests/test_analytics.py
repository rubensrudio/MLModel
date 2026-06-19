from fastapi.testclient import TestClient

from mlmodel.main import create_app


def test_crossplot_returns_points_for_selected_axes() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/crossplot",
        json={
            "x_field": "porosity_percent",
            "y_field": "vp_m_s",
            "color_by": "rock_type",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["x_field"] == "porosity_percent"
    assert payload["y_field"] == "vp_m_s"
    assert payload["color_by"] == "rock_type"
    assert len(payload["points"]) == 6
    assert payload["points"][0] == {
        "sample_code": "F244V",
        "x": 19.2,
        "y": 4339.0,
        "color": "Boundstone",
    }


def test_crossplot_rejects_unknown_numeric_field() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/crossplot",
        json={
            "x_field": "unknown",
            "y_field": "vp_m_s",
        },
    )

    assert response.status_code == 422
