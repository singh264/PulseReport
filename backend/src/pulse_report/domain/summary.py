from __future__ import annotations

from dataclasses import dataclass

from .pcr import Pcr


class SummaryFormatter:
    def format(self, pcr: Pcr) -> str:  # pragma: no cover (interface)
        raise NotImplementedError


@dataclass(frozen=True)
class PlainTextSummaryFormatter(SummaryFormatter):
    def format(self, pcr: Pcr) -> str:
        lines: list[str] = []
        lines.append(f"Event: {pcr.event_name}")
        lines.append(f"Report: {pcr.report_date.isoformat()} {pcr.report_time.strftime('%H:%M')}")
        lines.append(f"Patient: {pcr.patient.full_name} | DOB: {pcr.patient.date_of_birth.isoformat()} | Sex: {pcr.patient.sex.value}")
        lines.append(f"Consent: {pcr.consent.value}")
        lines.append("")
        lines.append("History/Description:")
        lines.append(pcr.history_description.strip())
        lines.append("")
        lines.append("Initial Vitals:")
        for vs in pcr.initial_vitals:
            pupils = f"L={'+' if vs.pupils.left_reactive else '-'} R={'+' if vs.pupils.right_reactive else '-'}"
            lines.append(
                f"- {vs.observed_at.strftime('%Y-%m-%d %H:%M')} | "
                f"Pulse {vs.pulse_bpm} | Resp {vs.resp_per_min} | "
                f"BP {vs.systolic_bp}/{vs.diastolic_bp} | LOC {vs.loc.value} | "
                f"Pain {vs.pain_0_to_10}/10 | Pupils {pupils}"
            )

        lines.append("")
        lines.append("Treatment:")
        if pcr.treatments:
            for t in pcr.treatments:
                lines.append(f"- {t.performed_at.strftime('%Y-%m-%d %H:%M')} | {t.intervention} | {t.results_notes}".strip())
        else:
            lines.append("- None recorded")

        lines.append("")
        lines.append("Disposition:")
        if pcr.disposition is None:
            lines.append("- Not documented")
        else:
            lines.append(
                f"- Discharge {pcr.disposition.discharge_time.strftime('%H:%M')} | "
                f"{pcr.disposition.disposition} | "
                f"Accompanied by {pcr.disposition.accompanied_by.value}"
            )
            if pcr.disposition.discharge_instructions.strip():
                lines.append(f"- Instructions: {pcr.disposition.discharge_instructions.strip()}")

        return "\n".join(lines)

