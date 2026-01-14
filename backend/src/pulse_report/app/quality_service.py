from __future__ import annotations

from dataclasses import dataclass

from pulse_report.app.repository import PcrRepository
from pulse_report.domain.quality import (
    DocumentationQualityEngine,
    DocumentationQualityReport,
    DispositionMissingInstructionsRule,
    VitalsChronologyRule,
    VitalsPlausibilityRule,
    DispositionNotDocumentedRule,
)


@dataclass
class QualityService:
    repo: PcrRepository
    engine: DocumentationQualityEngine

    @classmethod
    def default(cls, repo: PcrRepository) -> "QualityService":
        engine = DocumentationQualityEngine(
            rules=[
                DispositionNotDocumentedRule(),
                DispositionMissingInstructionsRule(),
                VitalsPlausibilityRule(),
                VitalsChronologyRule(),
            ]
        )
        return cls(repo=repo, engine=engine)

    def evaluate(self, pcr_id: str) -> DocumentationQualityReport:
        pcr = self.repo.get(pcr_id)
        if pcr is None:
            raise KeyError(f"PCR not found: {pcr_id}")
        return self.engine.evaluate(pcr)

