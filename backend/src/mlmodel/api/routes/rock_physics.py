from fastapi import APIRouter

from mlmodel.schemas.rock_physics import (
    AkiRichardsRequest,
    AkiRichardsResponse,
    GassmannRequest,
    GassmannResponse,
    GranularMediaRequest,
    GranularMediaResponse,
)
from mlmodel.services.rock_physics_service import RockPhysicsService

router = APIRouter(prefix="/models/rockphypy", tags=["rock physics"])


@router.post("/gassmann/run", response_model=GassmannResponse)
def run_gassmann(request: GassmannRequest) -> GassmannResponse:
    return RockPhysicsService().run_gassmann(request)


@router.post("/softsand/run", response_model=GranularMediaResponse)
def run_softsand(request: GranularMediaRequest) -> GranularMediaResponse:
    return RockPhysicsService().run_softsand(request)


@router.post("/stiffsand/run", response_model=GranularMediaResponse)
def run_stiffsand(request: GranularMediaRequest) -> GranularMediaResponse:
    return RockPhysicsService().run_stiffsand(request)


@router.post("/avo/aki-richards/run", response_model=AkiRichardsResponse)
def run_aki_richards(request: AkiRichardsRequest) -> AkiRichardsResponse:
    return RockPhysicsService().run_aki_richards(request)
