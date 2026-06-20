from typing import Protocol

from mlmodel.schemas.analyses import SavedAnalysis, SavedAnalysisCreate


class AnalysisRepository(Protocol):
    def create_analysis(self, analysis: SavedAnalysisCreate) -> SavedAnalysis:
        """Persist and return a saved analysis."""

    def list_analyses(self) -> list[SavedAnalysis]:
        """Return saved analyses."""

    def get_analysis(self, analysis_id: str) -> SavedAnalysis | None:
        """Return one saved analysis by id."""
