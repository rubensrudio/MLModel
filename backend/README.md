# MLModel Backend

Backend Python do WebLab Petrofisico / MLModel.

## Desenvolvimento local

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
uvicorn mlmodel.main:app --reload
```

O primeiro incremento expõe apenas o health check:

```text
GET /health
```
