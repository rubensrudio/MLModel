from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mlmodel.schemas.rock_physics import GassmannRequest


class ModelRunCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str = Field(min_length=1, max_length=120)
    model_version: str | None = None
    engine: str | None = None
    parameters: dict[str, Any]
    result: dict[str, Any]
    assumptions: list[str] = Field(default_factory=list)
    saved_analysis_id: str | None = None
    mlflow_run_id: str | None = None


class ModelRun(ModelRunCreate):
    run_id: str
    created_at: datetime


class GassmannModelRunRequest(BaseModel):
    parameters: GassmannRequest
    saved_analysis_id: str | None = None
