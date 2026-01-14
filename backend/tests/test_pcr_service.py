from datetime import date, datetime, time

import pytest

from pulse_report.app.repository import InMemoryPcrRepository
from pulse_report.app.service import PcrService
from pulse_report.domain.pcr import (
    AccompaniedBy,
    ConsentStatus,
    Disposition,
    LocLevel,
    PatientInfo,
    Pupils,
    Sex,
    TreatmentEntry,
    VitalSigns,
)


def test_create_pcr_persists_and_returns_id():
    repo = InMemoryPcrRepository()
    service = PcrService(repo=repo)

    patient = PatientInfo(
        full_name="Jane Doe",
        date_of_birth=date(2000, 1, 15),
        sex=Sex.FEMALE,
        phone="555-123-4567",
    )

    vs0 = VitalSigns(
        observed_at=datetime(2026, 1, 2, 10, 15),
        pulse_bpm=92,
        resp_per_min=18,
        systolic_bp=124,
        diastolic_bp=78,
        skin="Warm, dry",
        loc=LocLevel.ALERT,
        pain_0_to_10=2,
        pupils=Pupils(left_reactive=True, right_reactive=True),
    )

    treatment = [
        TreatmentEntry(
            performed_at=datetime(2026, 1, 2, 10, 20),
            intervention="Oxygen",
            results_notes="Improved SpO2 subjectively",
        )
    ]

    pcr_id = service.create_pcr(
        event_name="Community Event",
        report_date=date(2026, 1, 2),
        report_time=time(10, 30),
        patient=patient,
        consent=ConsentStatus.GIVEN,
        history_description="Felt dizzy after standing up quickly.",
        initial_vitals=[vs0],
        treatments=treatment,
        disposition=Disposition(
            discharge_time=time(11, 0),
            disposition="Back to Event",
            accompanied_by=AccompaniedBy.SELF,
            discharge_instructions="Hydrate, rest, return if symptoms worsen.",
        ),
    )

    loaded = repo.get(pcr_id)
    assert loaded is not None
    assert loaded.patient.full_name == "Jane Doe"
    assert loaded.event_name == "Community Event"
    assert loaded.consent == ConsentStatus.GIVEN


def test_export_summary_contains_key_sections():
    repo = InMemoryPcrRepository()
    service = PcrService(repo=repo)

    patient = PatientInfo(
        full_name="John Smith",
        date_of_birth=date(1995, 6, 1),
        sex=Sex.MALE,
        phone="555-000-0000",
    )

    vs0 = VitalSigns(
        observed_at=datetime(2026, 1, 2, 9, 5),
        pulse_bpm=110,
        resp_per_min=22,
        systolic_bp=140,
        diastolic_bp=90,
        skin="Pale",
        loc=LocLevel.VERBAL,
        pain_0_to_10=6,
        pupils=Pupils(left_reactive=True, right_reactive=False),
    )

    pcr_id = service.create_pcr(
        event_name="Watch Party",
        report_date=date(2026, 1, 2),
        report_time=time(9, 20),
        patient=patient,
        consent=ConsentStatus.REFUSED,
        history_description="Twisted ankle; swelling present.",
        initial_vitals=[vs0],
        treatments=[],
        disposition=None,
    )

    summary = service.export_summary(pcr_id)
    assert "Event:" in summary
    assert "Patient:" in summary
    assert "Consent:" in summary
    assert "Initial Vitals:" in summary
    assert "Pulse" in summary
    assert "Disposition:" in summary  # should still print section even if None


def test_validation_rejects_out_of_range_pain_score():
    repo = InMemoryPcrRepository()
    service = PcrService(repo=repo)

    patient = PatientInfo(
        full_name="Invalid Pain",
        date_of_birth=date(2001, 1, 1),
        sex=Sex.OTHER,
        phone="555",
    )

    with pytest.raises(ValueError):
        bad_vs = VitalSigns(
            observed_at=datetime(2026, 1, 2, 12, 0),
            pulse_bpm=80,
            resp_per_min=16,
            systolic_bp=120,
            diastolic_bp=80,
            skin="Normal",
            loc=LocLevel.ALERT,
            pain_0_to_10=11,  # invalid
            pupils=Pupils(left_reactive=True, right_reactive=True),
        )

        service.create_pcr(
            event_name="Test",
            report_date=date(2026, 1, 2),
            report_time=time(12, 5),
            patient=patient,
            consent=ConsentStatus.GIVEN,
            history_description="N/A",
            initial_vitals=[bad_vs],
            treatments=[],
            disposition=None,
        )

def test_update_disposition_updates_existing_discharge_instructions():
    repo = InMemoryPcrRepository()
    service = PcrService(repo=repo)

    patient = PatientInfo(
        full_name="Jane Doe",
        date_of_birth=date(2000, 1, 15),
        sex=Sex.FEMALE,
        phone="555-123-4567",
    )

    vs0 = VitalSigns(
        observed_at=datetime(2026, 1, 2, 10, 15),
        pulse_bpm=92,
        resp_per_min=18,
        systolic_bp=124,
        diastolic_bp=78,
        skin="Warm, dry",
        loc=LocLevel.ALERT,
        pain_0_to_10=2,
        pupils=Pupils(left_reactive=True, right_reactive=True),
    )

    pcr_id = service.create_pcr(
        event_name="Community Event",
        report_date=date(2026, 1, 2),
        report_time=time(10, 30),
        patient=patient,
        consent=ConsentStatus.GIVEN,
        history_description="Felt dizzy after standing up quickly.",
        initial_vitals=[vs0],
        treatments=[],
        disposition=Disposition(
            discharge_time=time(11, 0),
            disposition="Home",
            accompanied_by=AccompaniedBy.SELF,
            discharge_instructions="",
        ),
    )

    updated = service.update_disposition(
        pcr_id,
        discharge_instructions="Hydrate, rest, return if symptoms worsen.",
    )

    assert updated.disposition is not None
    assert updated.disposition.discharge_instructions == "Hydrate, rest, return if symptoms worsen."

