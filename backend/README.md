# MLModel Backend

Python backend for WebLab Petrophysics / MLModel.

## Local Development

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
uvicorn mlmodel.main:app --reload
```

The first increment exposes only the health check:

```text
GET /health
```
