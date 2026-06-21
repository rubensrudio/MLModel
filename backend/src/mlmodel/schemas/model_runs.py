from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mlmodel.schemas.rock_physics import AkiRichardsRequest, GassmannRequest, GranularMediaRequest

RockPhyPyBatchModel = Literal["gassmann", "softsand", "stiffsand", "avo.aki-richards"]


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


class GranularMediaModelRunRequest(BaseModel):
    parameters: GranularMediaRequest
    saved_analysis_id: str | None = None


class AkiRichardsModelRunRequest(BaseModel):
    parameters: AkiRichardsRequest
    saved_analysis_id: str | None = None


class RockPhyPyBatchModelRunRequest(BaseModel):
    model: RockPhyPyBatchModel
    rows: list[dict[str, Any]] | None = Field(default=None, min_length=1)
    csv_text: str | None = Field(default=None, min_length=1)
    saved_analysis_id: str | None = None

    @model_validator(mode="after")
    def validate_single_batch_input(self) -> "RockPhyPyBatchModelRunRequest":
        if bool(self.rows) == bool(self.csv_text):
            raise ValueError("Provide exactly one batch input: rows or csv_text.")
        return self
