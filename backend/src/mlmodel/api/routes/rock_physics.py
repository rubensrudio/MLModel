from fastapi import APIRouter

from mlmodel.schemas.rock_physics import GassmannRequest, GassmannResponse
from mlmodel.services.rock_physics_service import RockPhysicsService

router = APIRouter(prefix="/models/rockphypy", tags=["rock physics"])


@router.post("/gassmann/run", response_model=GassmannResponse)
def run_gassmann(request: GassmannRequest) -> GassmannResponse:
    return RockPhysicsService().run_gassmann(request)
