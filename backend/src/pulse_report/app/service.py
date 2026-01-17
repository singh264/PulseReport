from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, time
from typing import Optional

from pulse_report.domain.pcr import (
    ConsentStatus,
    Disposition,
    PatientInfo,
    Pcr,
    TreatmentEntry,
    VitalSigns,
    AccompaniedBy,
)
from pulse_report.domain.summary import PlainTextSummaryFormatter, SummaryFormatter

from .repository import PcrRepository


@dataclass
class PcrService:
    repo: PcrRepository
    formatter: SummaryFormatter = PlainTextSummaryFormatter()

    def create_pcr(
        self,
        *,
        event_name: str,
        report_date: date,
        report_time: time,
        patient: PatientInfo,
        consent: ConsentStatus,
        history_description: str,
        initial_vitals: list[VitalSigns],
        treatments: list[TreatmentEntry],
        disposition: Optional[Disposition],
    ) -> str:
        pcr_id = self._new_id()
        pcr = Pcr(
            pcr_id=pcr_id,
            event_name=event_name,
            report_date=report_date,
            report_time=report_time,
            patient=patient,
            consent=consent,
            history_description=history_description,
            initial_vitals=initial_vitals,
            treatments=treatments,
            disposition=disposition,
        )
        self.repo.save(pcr)
        return pcr_id

    def export_summary(self, pcr_id: str) -> str:
        pcr = self.repo.get(pcr_id)
        if pcr is None:
            raise KeyError(f"PCR not found: {pcr_id}")
        return self.formatter.format(pcr)

    @staticmethod
    def _new_id() -> str:
        return str(uuid.uuid4())

    def update_disposition(
        self,
        pcr_id: str,
        *,
        discharge_time: time | None = None,
        disposition: str | None = None,
        accompanied_by: "AccompaniedBy | None" = None,
        discharge_instructions: str | None = None,
    ) -> Pcr:
        pcr = self.repo.get(pcr_id)
        if pcr is None:
            raise KeyError(f"PCR not found: {pcr_id}")

        pcr.update_disposition(
            discharge_time=discharge_time,
            disposition=disposition,
            accompanied_by=accompanied_by,
            discharge_instructions=discharge_instructions,
        )

        # For future Postgres repo, save() makes persistence explicit
        self.repo.save(pcr)
        return pcr

    def list_pcrs(self, *, limit: int = 50, offset: int = 0) -> list[Pcr]:
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        if offset < 0:
            raise ValueError("offset must be >= 0")

        pcrs = self.repo.list()

        # Deterministic sort for “inbox” view
        pcrs_sorted = sorted(
            pcrs,
            key=lambda p: (p.report_date, p.report_time, p.pcr_id),
            reverse=True,
        )

        return pcrs_sorted[offset : offset + limit]

    def add_vital(self, pcr_id: str, vital: VitalSigns) -> Pcr:
        pcr = self.repo.get(pcr_id)
        if pcr is None:
            raise KeyError(f"PCR not found: {pcr_id}")

        pcr.add_vital(vital)
        self.repo.save(pcr)
        return pcr

