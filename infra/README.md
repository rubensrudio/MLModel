# Infrastructure

Local infrastructure for MLModel development.

## PostgreSQL

The backend automatically uses PostgreSQL when these environment variables exist:

```powershell
$env:POSTGRESQL_HOST = "localhost"
$env:POSTGRESQL_PORT = "5432"
$env:POSTGRESQL_USER = "mlmodel"
$env:POSTGRESQL_PASSWORD = "mlmodel"
```

The default database is `mlmodel`. Use `MLMODEL_POSTGRESQL_DATABASE` only if you need to override it.
The default schema is `public`; use `MLMODEL_POSTGRESQL_SCHEMA` only if you need to override it.

You can also use `MLMODEL_DATABASE_URL` as a full connection string. `infra/docker-compose.yml`
exists only as an optional utility for developers without an available PostgreSQL instance.
Use `MLMODEL_ANALYSIS_REPOSITORY_BACKEND=local` only if you want to force in-memory persistence even
when PostgreSQL variables are present.

Without these variables, the backend uses local in-memory persistence for saved analyses.

Diagnostics:

```text
GET /health/persistence
```

Manual query:

```sql
select table_schema, table_name
from information_schema.tables
where table_name = 'saved_analyses';
```

## MLflow

MLflow has not been added to Compose yet. The integration should be added after model runs and
parameter/metric tracking are defined in the backend.
