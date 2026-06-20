from mlmodel.repositories.analysis_repository import AnalysisRepository
from mlmodel.schemas.analyses import SavedAnalysis, SavedAnalysisCreate


class AnalysisService:
    def __init__(self, repository: AnalysisRepository) -> None:
        self._repository = repository

    def create_analysis(self, analysis: SavedAnalysisCreate) -> SavedAnalysis:
        return self._repository.create_analysis(analysis)

    def list_analyses(self) -> list[SavedAnalysis]:
        return self._repository.list_analyses()

    def get_analysis(self, analysis_id: str) -> SavedAnalysis | None:
        return self._repository.get_analysis(analysis_id)
