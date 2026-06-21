# MLModel Frontend

Angular frontend shell for MLModel / WebLab Petrophysics.

## Local Development

Start the backend first:

```powershell
cd ..\backend
.\.venv\Scripts\Activate.ps1
uvicorn mlmodel.main:app --reload
```

Then start the frontend:

```powershell
cd ..\frontend
npm install
npm run dev
```

The dev server runs at:

```text
http://127.0.0.1:4200
```

The proxy forwards `/api` and `/health` to `http://127.0.0.1:8000`.

## Current Screen

The first shell includes:

- sample summary KPIs;
- well and rock-type filters;
- sample table;
- porosity x Vp crossplot from the backend;
- latest model-run summary and CSV export;
- Rock Physics execution forms for Gassmann, soft-sand, stiff-sand, and Aki-Richards;
- JSON/CSV batch execution.

The frontend does not calculate scientific results. It only sends parameters to the backend and
renders persisted responses.
