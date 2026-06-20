from pydantic import BaseModel


class PersistenceHealthResponse(BaseModel):
    backend: str
    database_url_configured: bool
    postgresql_host_configured: bool
    postgresql_database: str
    postgresql_schema: str
    table_name: str
    table_exists: bool | None
    current_database: str | None = None
    current_schema: str | None = None
    error: str | None = None
