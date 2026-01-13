from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from pulse_report.domain.pcr import Pcr


class Severity(str, Enum):
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


@dataclass(frozen=True)
class QualityIssue:
    code: str
    message: str
    severity: Severity = Severity.WARNING


@dataclass(frozen=True)
class DocumentationQualityReport:
    issues: list[QualityIssue]

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)


class QualityRule(Protocol):
    def evaluate(self, pcr: Pcr) -> list[QualityIssue]: ...


@dataclass(frozen=True)
class DispositionMissingInstructionsRule:
    def evaluate(self, pcr: Pcr) -> list[QualityIssue]:
        if pcr.disposition is None:
            return []
        if pcr.disposition.discharge_instructions.strip():
            return []
        return [
            QualityIssue(
                code="DISPOSITION_MISSING_INSTRUCTIONS",
                message="Disposition is documented but discharge instructions are missing.",
                severity=Severity.WARNING,
            )
        ]


@dataclass(frozen=True)
class VitalsChronologyRule:
    def evaluate(self, pcr: Pcr) -> list[QualityIssue]:
        times = [v.observed_at for v in pcr.initial_vitals]
        if times == sorted(times):
            return []
        return [
            QualityIssue(
                code="VITALS_OUT_OF_ORDER",
                message="Initial vitals timestamps are not in chronological order.",
                severity=Severity.WARNING,
            )
        ]


@dataclass(frozen=True)
class VitalsPlausibilityRule:
    """
    Simple, non-diagnostic plausibility bounds (not age-specific yet).
    These are meant for documentation QA, not clinical decision-making.
    """
    min_pulse: int = 20
    max_pulse: int = 250
    min_resp: int = 4
    max_resp: int = 80
    min_sys: int = 50
    max_sys: int = 250
    min_dia: int = 20
    max_dia: int = 150

    def evaluate(self, pcr: Pcr) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        for idx, v in enumerate(pcr.initial_vitals):
            if v.pulse_bpm < self.min_pulse or v.pulse_bpm > self.max_pulse:
                issues.append(
                    QualityIssue(
                        code="VITALS_IMPLAUSIBLE_PULSE",
                        message=f"Vitals[{idx}] pulse looks implausible: {v.pulse_bpm} bpm.",
                        severity=Severity.WARNING,
                    )
                )
            if v.resp_per_min < self.min_resp or v.resp_per_min > self.max_resp:
                issues.append(
                    QualityIssue(
                        code="VITALS_IMPLAUSIBLE_RESP",
                        message=f"Vitals[{idx}] respiratory rate looks implausible: {v.resp_per_min}/min.",
                        severity=Severity.WARNING,
                    )
                )
            if v.systolic_bp < self.min_sys or v.systolic_bp > self.max_sys:
                issues.append(
                    QualityIssue(
                        code="VITALS_IMPLAUSIBLE_SYSTOLIC_BP",
                        message=f"Vitals[{idx}] systolic BP looks implausible: {v.systolic_bp}.",
                        severity=Severity.WARNING,
                    )
                )
            if v.diastolic_bp < self.min_dia or v.diastolic_bp > self.max_dia:
                issues.append(
                    QualityIssue(
                        code="VITALS_IMPLAUSIBLE_DIASTOLIC_BP",
                        message=f"Vitals[{idx}] diastolic BP looks implausible: {v.diastolic_bp}.",
                        severity=Severity.WARNING,
                    )
                )
        return issues


@dataclass(frozen=True)
class DocumentationQualityEngine:
    rules: list[QualityRule]

    def evaluate(self, pcr: Pcr) -> DocumentationQualityReport:
        issues: list[QualityIssue] = []
        for r in self.rules:
            issues.extend(r.evaluate(pcr))
        return DocumentationQualityReport(issues=issues)

