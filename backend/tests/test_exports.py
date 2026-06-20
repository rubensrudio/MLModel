from fastapi.testclient import TestClient

from mlmodel.main import create_app


def test_export_samples_json_returns_filtered_rows() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/exports/samples/json",
        json={
            "filters": {
                "wells": ["1-RJS-628"],
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["row_count"] == 2
    assert [row["sample_code"] for row in payload["rows"]] == ["F244V", "G2441V"]


def test_export_samples_csv_returns_filtered_csv() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/exports/samples/csv",
        json={
            "filters": {
                "rock_types": ["Floatstone"],
            }
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="samples.csv"'

    lines = response.text.strip().splitlines()
    assert lines[0] == (
        "sample_code,well,depth_m,porosity_fraction,permeability_md,"
        "rock_type,lithology_micro,vp_m_s,confining_pressure_psi"
    )
    assert lines[1] == (
        "G2441V,1-RJS-628,4917.1,0.199,674.0,Floatstone,"
        "COQUINA FRAGMENTADA,4291.0,7500.0"
    )


def test_export_crossplot_json_returns_filtered_analytics_payload() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/exports/analytics/crossplot/json",
        json={
            "x_field": "porosity_percent",
            "y_field": "vp_m_s",
            "filters": {
                "sample_codes": ["G2441V"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["points"]) == 1
    assert payload["points"][0]["sample_code"] == "G2441V"
    assert payload["indicators"] == {
        "sample_count": 1,
        "pearson_correlation": None,
        "mean_absolute_error": None,
    }


def test_export_crossplot_csv_returns_chart_points() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/exports/analytics/crossplot/csv",
        json={
            "x_field": "porosity_percent",
            "y_field": "vp_m_s",
            "filters": {
                "sample_codes": ["G2441V"],
            },
        },
    )

    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert lines == [
        "sample_code,x,y,color",
        "G2441V,19.900000000000002,4291.0,",
    ]


def test_export_histogram_json_returns_filtered_bins() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/exports/analytics/histogram/json",
        json={
            "field": "vp_m_s",
            "bins": 2,
            "filters": {
                "wells": ["1-RJS-628"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 2
    assert [bin_["count"] for bin_ in payload["bins"]] == [1, 1]


def test_export_histogram_csv_returns_grouped_bins() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/exports/analytics/histogram/csv",
        json={
            "field": "vp_m_s",
            "bins": 1,
            "group_by": "rock_type",
            "filters": {
                "wells": ["1-RJS-628"],
            },
        },
    )

    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert lines == [
        "group,start,end,count",
        "Boundstone,4339.0,4339.0,1",
        "Floatstone,4291.0,4291.0,1",
    ]


def test_export_boxplot_json_returns_grouped_series() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/exports/analytics/boxplot/json",
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


def test_export_boxplot_csv_returns_series_statistics() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/exports/analytics/boxplot/csv",
        json={
            "field": "vp_m_s",
            "group_by": "well",
            "filters": {
                "wells": ["1-RJS-628"],
            },
        },
    )

    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert lines[0] == (
        "group,count,minimum,q1,median,q3,maximum,mean,standard_deviation,"
        "coefficient_variation_percent,p10,p50,p90"
    )
    assert lines[1].startswith("1-RJS-628,2,4291.0,4303.0,4315.0,4327.0,4339.0,4315.0")
