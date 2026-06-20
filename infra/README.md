# Infraestrutura

Infraestrutura local para desenvolvimento do MLModel.

## PostgreSQL

O backend usa automaticamente PostgreSQL quando estas variaveis existem no ambiente:

```powershell
$env:POSTGRESQL_HOST = "localhost"
$env:POSTGRESQL_PORT = "5432"
$env:POSTGRESQL_USER = "mlmodel"
$env:POSTGRESQL_PASSWORD = "mlmodel"
```

O database padrao e `mlmodel`. Use `MLMODEL_POSTGRESQL_DATABASE` apenas se precisar sobrescrever.
O schema padrao e `public`; use `MLMODEL_POSTGRESQL_SCHEMA` apenas se precisar sobrescrever.

Tambem e possivel usar `MLMODEL_DATABASE_URL` como connection string completa. O
`infra/docker-compose.yml` existe apenas como utilitario opcional para desenvolvedores sem um
PostgreSQL disponivel.
Use `MLMODEL_ANALYSIS_REPOSITORY_BACKEND=local` apenas se quiser forcar persistencia em memoria mesmo
com variaveis PostgreSQL presentes.

Sem essas variaveis, o backend usa persistencia local em memoria para saved analyses.

Diagnostico:

```text
GET /health/persistence
```

Consulta manual:

```sql
select table_schema, table_name
from information_schema.tables
where table_name = 'saved_analyses';
```

## MLflow

MLflow ainda nao foi adicionado ao Compose. A integracao deve entrar depois que model runs e
rastreamento de parametros/metricas estiverem definidos no backend.
