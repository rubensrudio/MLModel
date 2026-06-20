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
    assert payload["indicators"]["sample_count"] == 6
    assert round(payload["indicators"]["pearson_correlation"], 3) == 0.236
    assert payload["indicators"]["mean_absolute_error"] is None


def test_crossplot_applies_filters() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/crossplot",
        json={
            "x_field": "porosity_percent",
            "y_field": "vp_m_s",
            "filters": {
                "wells": ["1-RJS-628"],
                "rock_types": ["Floatstone"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [point["sample_code"] for point in payload["points"]] == ["G2441V"]
    assert payload["indicators"] == {
        "sample_count": 1,
        "pearson_correlation": None,
        "mean_absolute_error": None,
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


def test_crossplot_compare_returns_prediction_errors_and_mae() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/crossplot/compare",
        json={
            "x_field": "porosity_percent",
            "y_field": "vp_m_s",
            "color_by": "rock_type",
            "predictions": [
                {"sample_code": "F244V", "predicted_y": 4300.0},
                {"sample_code": "G2441V", "predicted_y": 4200.0},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["x_field"] == "porosity_percent"
    assert payload["y_field"] == "vp_m_s"
    assert payload["color_by"] == "rock_type"
    assert len(payload["points"]) == 2
    assert payload["points"][0] == {
        "sample_code": "F244V",
        "x": 19.2,
        "y": 4339.0,
        "color": "Boundstone",
        "predicted_y": 4300.0,
        "absolute_error": 39.0,
    }
    assert payload["points"][1]["absolute_error"] == 91.0
    assert payload["indicators"]["sample_count"] == 2
    assert payload["indicators"]["mean_absolute_error"] == 65.0


def test_crossplot_compare_applies_filters_before_matching_predictions() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/crossplot/compare",
        json={
            "x_field": "porosity_percent",
            "y_field": "vp_m_s",
            "filters": {
                "sample_codes": ["G2441V"],
            },
            "predictions": [
                {"sample_code": "F244V", "predicted_y": 4300.0},
                {"sample_code": "G2441V", "predicted_y": 4200.0},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [point["sample_code"] for point in payload["points"]] == ["G2441V"]
    assert payload["indicators"]["mean_absolute_error"] == 91.0


def test_crossplot_compare_returns_empty_result_when_no_predictions_match() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/crossplot/compare",
        json={
            "x_field": "porosity_percent",
            "y_field": "vp_m_s",
            "predictions": [
                {"sample_code": "UNKNOWN", "predicted_y": 4200.0},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["points"] == []
    assert payload["indicators"] == {
        "sample_count": 0,
        "pearson_correlation": None,
        "mean_absolute_error": None,
    }


def test_histogram_returns_counted_bins_for_selected_field() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/histogram",
        json={
            "field": "porosity_percent",
            "bins": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["field"] == "porosity_percent"
    assert payload["group_by"] is None
    assert payload["sample_count"] == 6
    assert round(payload["stats"]["mean"], 2) == 21.22
    assert round(payload["stats"]["p10"], 2) == 18.2
    assert round(payload["stats"]["p50"], 2) == 21.55
    assert round(payload["stats"]["p90"], 2) == 23.9
    assert len(payload["bins"]) == 3
    assert [bin_["count"] for bin_ in payload["bins"]] == [2, 1, 3]
    assert round(payload["bins"][0]["start"], 1) == 17.2
    assert round(payload["bins"][-1]["end"], 1) == 24.5
    assert payload["series"] == []


def test_histogram_can_group_by_category() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/histogram",
        json={
            "field": "vp_m_s",
            "bins": 2,
            "group_by": "rock_type",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    groups = {series["group"]: series for series in payload["series"]}
    assert payload["group_by"] == "rock_type"
    assert groups["Boundstone"]["sample_count"] == 2
    assert groups["Boundstone"]["stats"]["count"] == 2
    assert round(groups["Boundstone"]["stats"]["mean"], 1) == 4184.5
    assert groups["Mudstone"]["sample_count"] == 1
    assert groups["Mudstone"]["bins"][0]["count"] == 1


def test_histogram_applies_filters_before_counting_bins() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/histogram",
        json={
            "field": "porosity_percent",
            "bins": 2,
            "filters": {
                "min_porosity_percent": 23,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 3
    assert payload["stats"]["count"] == 3
    assert [bin_["count"] for bin_ in payload["bins"]] == [2, 1]


def test_histogram_rejects_invalid_bin_count() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/histogram",
        json={
            "field": "vp_m_s",
            "bins": 0,
        },
    )

    assert response.status_code == 422


def test_boxplot_returns_statistics_for_selected_field() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/boxplot",
        json={
            "field": "porosity_percent",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["field"] == "porosity_percent"
    assert payload["group_by"] is None
    assert len(payload["series"]) == 1

    series = payload["series"][0]
    assert series["group"] is None
    assert series["count"] == 6
    assert round(series["minimum"], 1) == 17.2
    assert round(series["q1"], 2) == 19.38
    assert round(series["median"], 2) == 21.55
    assert round(series["q3"], 2) == 23.28
    assert round(series["maximum"], 1) == 24.5
    assert round(series["mean"], 2) == 21.22
    assert round(series["stats"]["p10"], 2) == 18.2
    assert round(series["stats"]["p90"], 2) == 23.9


def test_boxplot_can_group_by_category() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/boxplot",
        json={
            "field": "vp_m_s",
            "group_by": "rock_type",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    groups = {series["group"]: series for series in payload["series"]}

    assert groups["Boundstone"]["count"] == 2
    assert round(groups["Boundstone"]["minimum"], 1) == 4030.0
    assert round(groups["Boundstone"]["maximum"], 1) == 4339.0
    assert groups["Mudstone"]["count"] == 1
    assert groups["Mudstone"]["median"] == 6455.0


def test_boxplot_applies_filters_before_grouping() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analytics/boxplot",
        json={
            "field": "vp_m_s",
            "group_by": "well",
            "filters": {
                "wells": ["1-RJS-628"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["series"]) == 1
    assert payload["series"][0]["group"] == "1-RJS-628"
    assert payload["series"][0]["count"] == 2
