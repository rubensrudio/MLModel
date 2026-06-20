# MLModel / WebLab Petrophysics

MLModel is the initial backend foundation for a WebLab Petrophysics application.

The current implementation focuses on a tested Python API for petrophysical sample exploration,
basic analytics, unit conversions, and the first rock physics model endpoint.

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
- First rock physics endpoint for a critical-porosity + Gassmann workflow
- Automated tests for every implemented increment
- Ruff lint configuration

Not implemented yet:

- Frontend application
- PostgreSQL persistence
- MLflow Tracking Server integration
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
34 passed
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
The current implementation uses local in-memory persistence behind a repository interface. It is
intended as the API contract before PostgreSQL is introduced.

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

1. Replace saved-analysis in-memory persistence with PostgreSQL-backed persistence.
2. Add local Docker Compose for PostgreSQL and MLflow.
3. Add MAE when model/reference prediction series are available.
4. Add PNG export support later when frontend chart rendering exists.
5. Resolve the RockPhyPy/Matplotlib compatibility issue.
6. Add `softsand` and `AVO` model endpoints.
