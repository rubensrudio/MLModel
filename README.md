# MLModel / WebLab Petrophysics

MLModel is the initial backend foundation for a WebLab Petrophysics application.

The current implementation focuses on a tested Python API for petrophysical sample exploration,
basic analytics, unit conversions, persisted saved analyses, persisted model runs, and optional
MLflow tracking.

## Current Status

Implemented so far:

- FastAPI backend project under `backend/`
- Health check endpoint
- Synthetic petrophysical sample fixtures
- Sample listing and summary endpoints
- Expanded sample detail endpoint
- Shared sample filters for listing, summary, crossplot, histogram, and boxplot
- Domain unit conversion helpers
- Generic crossplot analytics endpoint
- Histogram analytics endpoint with optional grouping and indicator stats
- Boxplot analytics endpoint with optional grouping and indicator stats
- JSON/CSV exports for filtered samples and analytics results
- Crossplot indicators with sample count and Pearson correlation
- Saved-analysis API with local in-memory persistence
- Model-run API with optional saved-analysis linkage
- Optional MLflow logging for model runs
- PostgreSQL persistence for saved analyses and model runs
- First rock physics endpoint for a critical-porosity + Gassmann workflow
- Automated tests for every implemented increment
- Ruff lint configuration

Not implemented yet:

- Frontend application
- DSIS/DSIF corporate data integration
- Authentication and authorization
- Production deployment configuration

## Repository Layout

```text
MLModel/
  backend/
    pyproject.toml
    README.md
    src/mlmodel/
      api/routes/
      core/
      repositories/
      schemas/
      services/
    tests/

  data/
    fixtures/
      samples.csv
      basic_petrophysics.csv
      petrography.csv
      mineralogy_total.csv
      mineralogy_clays.csv
      sonic_velocity.csv

  infra/
    README.md

  README.md
```

Local planning and documentation folders such as `.specs/`, `.claude/`, and `docs/` are intentionally
ignored by Git.

## Requirements

- Python 3.11 or newer
- Recommended: Python 3.12.x

The current environment was validated with:

```text
Python 3.12.9
```

## Setup

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

If the dependencies were already installed globally during development, the tests may run without a
virtual environment, but a local `.venv` is the recommended workflow.

### Windows venv Troubleshooting

If `python -m venv .venv` fails while running `ensurepip`, the `.venv` folder may have been created
only partially. Remove it and create the environment with `virtualenv` instead:

```powershell
cd backend

# Remove the broken partial environment if it exists.
Remove-Item -Recurse -Force .venv

# Install virtualenv using the global Python installation.
python -m pip install virtualenv

# Create a clean local environment.
python -m virtualenv .venv

# Activate and install project dependencies.
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

If PowerShell blocks activation because of execution policy, activate only for the current shell with:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

## Run Tests

From `backend/`:

```powershell
python -m pytest
```

Current expected result:

```text
55 passed
```

## Run Lint

From `backend/`:

```powershell
python -m ruff check .
```

Current expected result:

```text
All checks passed!
```

## Run the API Locally

From `backend/` with the virtual environment activated:

```powershell
uvicorn mlmodel.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

OpenAPI documentation:

```text
http://127.0.0.1:8000/docs
```

## Validated Local Runtime Flow

The following workflow was validated on 2026-06-20.

### PostgreSQL

The backend reads these environment variables from the shell running `uvicorn`:

```powershell
$env:POSTGRESQL_HOST = "<host>"
$env:POSTGRESQL_PORT = "<port>"
$env:POSTGRESQL_USER = "<user>"
$env:POSTGRESQL_PASSWORD = "<password>"
```

The backend ignores global `POSTGRESQL_DATABASE` and uses `mlmodel` by default. Use
`MLMODEL_POSTGRESQL_DATABASE` only if the project database name must differ from `mlmodel`.

Check runtime persistence selection:

```http
GET /health/persistence
```

Expected PostgreSQL fields:

```json
{
  "backend": "postgres",
  "postgresql_database": "mlmodel",
  "postgresql_schema": "public",
  "table_exists": true,
  "current_database": "mlmodel"
}
```

Expected tables:

```sql
select table_schema, table_name
from information_schema.tables
where table_name in ('saved_analyses', 'model_runs')
order by table_name;
```

### MLflow

Install dependencies inside the backend virtual environment:

```powershell
cd D:\Sistemas\MLModel\backend
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Start MLflow in a separate shell:

```powershell
mlflow server `
  --backend-store-uri sqlite:///mlflow.db `
  --default-artifact-root ./mlruns `
  --host 127.0.0.1 `
  --port 5000
```

Start the backend with MLflow enabled:

```powershell
$env:MLMODEL_MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
$env:MLMODEL_MLFLOW_EXPERIMENT_NAME = "MLModel Rock Physics"

uvicorn mlmodel.main:app --reload
```

Validate by calling:

```http
POST /api/model-runs/rockphypy/gassmann
```

The returned payload should include `mlflow_run_id`, the row in `public.model_runs` should persist
that id, and the MLflow UI at `http://127.0.0.1:5000` should show params, metrics, and the
`model_run.json` artifact.

## Implemented Endpoints

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "service": "MLModel API",
  "version": "0.1.0"
}
```

### List Samples

```http
GET /api/samples
```

Returns the current synthetic petrophysical samples from:

```text
data/fixtures/samples.csv
```

Each sample includes:

- sample code
- well
- depth in meters
- porosity as fraction
- permeability in mD
- rock type
- micro lithology
- `Vp` in m/s
- confining pressure in psi

Supported query filters:

- `sample_codes`
- `wells`
- `rock_types`
- `lithologies`
- `min_depth_m`
- `max_depth_m`
- `min_porosity_percent`
- `max_porosity_percent`
- `min_confining_pressure_psi`
- `max_confining_pressure_psi`

List filters can be repeated or comma-separated:

```http
GET /api/samples?wells=1-RJS-628&rock_types=Floatstone
GET /api/samples?sample_codes=F244V,G2441V
```

### Samples Summary

```http
GET /api/samples/summary
```

Returns dashboard-style KPIs:

- sample count
- well count
- rock type count
- min/max depth
- average porosity in percent
- average `Vp` in m/s

The same query filters supported by `GET /api/samples` can be used here.

### Sample Detail

```http
GET /api/samples/{sample_code}
```

Example:

```http
GET /api/samples/G2441V
```

Returns an expanded sample payload with:

- base sample data
- basic petrophysics
- petrography
- total DRX mineralogy
- clay DRX mineralogy
- sonic velocity

Unknown samples return:

```http
404 Not Found
```

### Crossplot Analytics

```http
POST /api/analytics/crossplot
POST /api/analytics/crossplot/compare
```

Example request:

```json
{
  "x_field": "porosity_percent",
  "y_field": "vp_m_s",
  "color_by": "rock_type",
  "filters": {
    "wells": ["1-RJS-628"],
    "rock_types": ["Floatstone"]
  }
}
```

Supported numeric fields:

- `depth_m`
- `porosity_percent`
- `permeability_md`
- `vp_m_s`
- `confining_pressure_psi`

Supported category fields:

- `well`
- `rock_type`
- `lithology_micro`

The response returns chart-ready points for a frontend charting library such as eCharts.

The response also includes `indicators`:

- `sample_count`
- `pearson_correlation`
- `mean_absolute_error`

`mean_absolute_error` is currently `null` because MAE requires a model or reference prediction
series. It should be populated when crossplot/model comparison is implemented.

Use `POST /api/analytics/crossplot/compare` when model/reference predictions are available per
sample. The endpoint matches predictions by `sample_code` and returns `predicted_y`,
`absolute_error`, and `indicators.mean_absolute_error`.

Example comparison request:

```json
{
  "x_field": "porosity_percent",
  "y_field": "vp_m_s",
  "color_by": "rock_type",
  "predictions": [
    {
      "sample_code": "F244V",
      "predicted_y": 4300.0
    }
  ]
}
```

### Histogram Analytics

```http
POST /api/analytics/histogram
```

Example request:

```json
{
  "field": "porosity_percent",
  "bins": 10,
  "group_by": "rock_type",
  "filters": {
    "min_porosity_percent": 20
  }
}
```

`group_by` is optional. When present, it can use:

- `well`
- `rock_type`
- `lithology_micro`

The response includes:

- aggregate bins
- grouped series when `group_by` is provided
- sample count
- mean
- median
- standard deviation
- coefficient of variation
- min/max
- P10/P50/P90

### Boxplot Analytics

```http
POST /api/analytics/boxplot
```

Example request:

```json
{
  "field": "vp_m_s",
  "group_by": "rock_type",
  "filters": {
    "wells": ["1-RJS-628"]
  }
}
```

The response includes one or more boxplot series with:

- minimum
- Q1
- median
- Q3
- maximum
- mean
- count
- P10/P50/P90 and other indicator stats

## Export Endpoints

All export endpoints use `POST` so they can receive the same filter and analytics request bodies used
by the interactive API.

### Samples Export

```http
POST /api/exports/samples/json
POST /api/exports/samples/csv
```

Example request:

```json
{
  "filters": {
    "wells": ["1-RJS-628"],
    "rock_types": ["Floatstone"]
  }
}
```

The JSON endpoint returns:

- `row_count`
- `rows`

The CSV endpoint returns `text/csv` with a `Content-Disposition` attachment header.

### Analytics Export

```http
POST /api/exports/analytics/crossplot/json
POST /api/exports/analytics/crossplot/csv

POST /api/exports/analytics/histogram/json
POST /api/exports/analytics/histogram/csv

POST /api/exports/analytics/boxplot/json
POST /api/exports/analytics/boxplot/csv
```

These endpoints accept the same request bodies as:

- `POST /api/analytics/crossplot`
- `POST /api/analytics/histogram`
- `POST /api/analytics/boxplot`

CSV exports flatten the chart-ready payload into tabular rows suitable for download or downstream
analysis.

## Saved Analysis Endpoints

Saved analyses persist analysis configuration and optional result snapshots for later retrieval.
The default implementation uses local in-memory persistence behind a repository interface. PostgreSQL
can be enabled through environment variables for local persistence testing.

```http
POST /api/analyses
GET /api/analyses
GET /api/analyses/{analysis_id}
```

Example request:

```json
{
  "title": "Porosity vs Vp review",
  "analysis_type": "crossplot",
  "configuration": {
    "x_field": "porosity_percent",
    "y_field": "vp_m_s",
    "color_by": "rock_type",
    "filters": {
      "wells": ["1-RJS-628"]
    }
  },
  "comments": [
    {
      "author": "petrophysics",
      "text": "Review high-porosity samples."
    }
  ],
  "selected_models": ["gassmann-critical-porosity"],
  "result": {
    "indicators": {
      "sample_count": 2
    }
  }
}
```

### PostgreSQL Persistence for Saved Analyses

By default, saved analyses use PostgreSQL automatically when the `POSTGRESQL_*` environment variables
are available. Without those variables, the API falls back to in-memory persistence.

Expected PostgreSQL environment variables:

```powershell
$env:POSTGRESQL_HOST = "localhost"
$env:POSTGRESQL_PORT = "5432"
$env:POSTGRESQL_USER = "mlmodel"
$env:POSTGRESQL_PASSWORD = "mlmodel"

cd ..\backend
uvicorn mlmodel.main:app --reload
```

`MLMODEL_DATABASE_URL` can still be used as a full connection string override.
`MLMODEL_POSTGRESQL_DATABASE` can be used to override the default database name, which is `mlmodel`.
`MLMODEL_ANALYSIS_REPOSITORY_BACKEND=local` can be used to force in-memory persistence even when
PostgreSQL variables are present.

The backend creates the `saved_analyses` table automatically during API startup when PostgreSQL is
selected.

To confirm what the backend selected, call:

```http
GET /health/persistence
```

Expected PostgreSQL response includes:

```json
{
  "backend": "postgres",
  "postgresql_database": "mlmodel",
  "postgresql_schema": "public",
  "table_name": "saved_analyses",
  "table_exists": true
}
```

If you inspect the database manually, check the schema explicitly:

```sql
select table_schema, table_name
from information_schema.tables
where table_name = 'saved_analyses';
```

Use `MLMODEL_POSTGRESQL_SCHEMA` if the table must be created outside `public`.

## Model Run Endpoints

Model runs persist model execution parameters and results. A run can optionally be linked to a saved
analysis through `saved_analysis_id`.

```http
POST /api/model-runs
GET /api/model-runs
GET /api/model-runs?saved_analysis_id={analysis_id}
GET /api/model-runs/{run_id}
GET /api/analyses/{analysis_id}/model-runs
POST /api/model-runs/rockphypy/gassmann
```

Example generic model run:

```json
{
  "model_name": "rockphypy.gassmann",
  "model_version": "0.1.0",
  "engine": "local-gassmann-fallback",
  "parameters": {
    "porosity_fraction": 0.2
  },
  "result": {
    "vp_m_s": 4659.0
  },
  "assumptions": [
    "Gassmann low-frequency fluid substitution"
  ],
  "saved_analysis_id": null
}
```

Example Gassmann run with persistence:

```json
{
  "parameters": {
    "mineral_bulk_modulus_gpa": 37.0,
    "mineral_shear_modulus_gpa": 44.0,
    "mineral_density_g_cm3": 2.65,
    "fluid_bulk_modulus_gpa": 2.2,
    "fluid_density_g_cm3": 1.0,
    "porosity_fraction": 0.2,
    "critical_porosity_fraction": 0.4
  },
  "saved_analysis_id": null
}
```

### Optional MLflow Logging

Model runs are logged to MLflow only when `MLMODEL_MLFLOW_TRACKING_URI` is configured:

```powershell
$env:MLMODEL_MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
$env:MLMODEL_MLFLOW_EXPERIMENT_NAME = "MLModel Rock Physics"
```

When enabled, the backend logs:

- model run parameters as MLflow params;
- numeric result fields as MLflow metrics;
- the full model run payload as `model_run.json`;
- the returned `mlflow_run_id` in the persisted `ModelRun`.

### Gassmann Rock Physics Model

```http
POST /api/models/rockphypy/gassmann/run
```

Example request:

```json
{
  "mineral_bulk_modulus_gpa": 37.0,
  "mineral_shear_modulus_gpa": 44.0,
  "mineral_density_g_cm3": 2.65,
  "fluid_bulk_modulus_gpa": 2.2,
  "fluid_density_g_cm3": 1.0,
  "porosity_fraction": 0.2,
  "critical_porosity_fraction": 0.4
}
```

The endpoint returns:

- dry bulk modulus
- dry shear modulus
- saturated bulk modulus
- saturated shear modulus
- bulk density
- `Vp`
- `Vs`
- acoustic impedance
- `Vp/Vs`
- calculation engine
- model assumptions

## RockPhyPy Compatibility Note

`rockphypy` is declared as a backend dependency. During the first implementation, the package
installed successfully, but importing `rockphypy` directly failed because its `QI.py` module defines a
Matplotlib color map that is rejected by the currently installed Matplotlib version.

To keep the backend usable and tested, the Gassmann endpoint currently:

1. Tries to use RockPhyPy.
2. Falls back to a local equivalent implementation for:
   - critical porosity dry frame
   - Gassmann fluid substitution
   - velocity and density calculation

The response field `engine` shows which path was used:

- `rockphypy`
- `local-gassmann-fallback`

This should be revisited before expanding to more RockPhyPy models such as `softsand`, `stiffsand`,
or `AVO`.

## Development Rules

- Add tests at the end of every implementation increment.
- Keep scientific calculations in backend services, not in the frontend.
- Keep units explicit in API contracts.
- Do not commit real sensitive data.
- Do not commit local planning documentation from `.specs/`, `.claude/`, or `docs/`.

## Next Recommended Steps

1. Add PNG export support later when frontend chart rendering exists.
2. Resolve the RockPhyPy/Matplotlib compatibility issue.
3. Add `softsand` and `AVO` model endpoints.
4. Start frontend only after the model-run/analytics contracts are stable.
