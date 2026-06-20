from datetime import UTC, datetime
from uuid import uuid4

from mlmodel.repositories.analysis_repository import AnalysisRepository
from mlmodel.schemas.analyses import SavedAnalysis, SavedAnalysisCreate

_ANALYSES: dict[str, SavedAnalysis] = {}


class LocalAnalysisRepository(AnalysisRepository):
    def create_analysis(self, analysis: SavedAnalysisCreate) -> SavedAnalysis:
        now = datetime.now(UTC)
        saved_analysis = SavedAnalysis(
            **analysis.model_dump(),
            analysis_id=str(uuid4()),
            created_at=now,
            updated_at=now,
        )
        _ANALYSES[saved_analysis.analysis_id] = saved_analysis
        return saved_analysis

    def list_analyses(self) -> list[SavedAnalysis]:
        return sorted(_ANALYSES.values(), key=lambda analysis: analysis.created_at)

    def get_analysis(self, analysis_id: str) -> SavedAnalysis | None:
        return _ANALYSES.get(analysis_id)
