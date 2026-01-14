from datetime import date, datetime, time

from pulse_report.domain.pcr import (
    AccompaniedBy,
    ConsentStatus,
    Disposition,
    LocLevel,
    PatientInfo,
    Pcr,
    Pupils,
    Sex,
    VitalSigns,
)
from pulse_report.domain.quality import (
    DocumentationQualityEngine,
    DispositionMissingInstructionsRule,
    VitalsChronologyRule,
    VitalsPlausibilityRule,
    DispositionNotDocumentedRule,
)


def test_quality_engine_flags_common_issues():
    engine = DocumentationQualityEngine(
        rules=[
            DispositionMissingInstructionsRule(),
            VitalsPlausibilityRule(),
            VitalsChronologyRule(),
        ]
    )

    patient = PatientInfo(full_name="John Doe", date_of_birth=date(2000, 1, 1), sex=Sex.MALE)

    # out-of-order + implausible pulse
    v1 = VitalSigns(
        observed_at=datetime(2026, 1, 2, 10, 30),
        pulse_bpm=300,  # implausible
        resp_per_min=18,
        systolic_bp=120,
        diastolic_bp=80,
        skin="Normal",
        loc=LocLevel.ALERT,
        pain_0_to_10=1,
        pupils=Pupils(True, True),
    )
    v0 = VitalSigns(
        observed_at=datetime(2026, 1, 2, 10, 15),
        pulse_bpm=90,
        resp_per_min=18,
        systolic_bp=120,
        diastolic_bp=80,
        skin="Normal",
        loc=LocLevel.ALERT,
        pain_0_to_10=1,
        pupils=Pupils(True, True),
    )

    pcr = Pcr(
        pcr_id="pcr-1",
        event_name="Test Event",
        report_date=date(2026, 1, 2),
        report_time=time(10, 45),
        patient=patient,
        consent=ConsentStatus.GIVEN,
        history_description="Test history",
        initial_vitals=[v1, v0],  # not sorted
        treatments=[],
        disposition=Disposition(
            discharge_time=time(11, 0),
            disposition="Home",
            accompanied_by=AccompaniedBy.SELF,
            discharge_instructions="",  # missing
        ),
    )

    report = engine.evaluate(pcr)
    codes = {i.code for i in report.issues}

    assert "DISPOSITION_MISSING_INSTRUCTIONS" in codes
    assert "VITALS_OUT_OF_ORDER" in codes
    assert "VITALS_IMPLAUSIBLE_PULSE" in codes

def test_quality_engine_flags_missing_disposition():
    engine = DocumentationQualityEngine(
        rules=[
            DispositionNotDocumentedRule(),
        ]
    )

    patient = PatientInfo(full_name="No Dispo", date_of_birth=date(2000, 1, 1), sex=Sex.UNKNOWN)
    v0 = VitalSigns(
        observed_at=datetime(2026, 1, 2, 10, 15),
        pulse_bpm=90,
        resp_per_min=18,
        systolic_bp=120,
        diastolic_bp=80,
        skin="Normal",
        loc=LocLevel.ALERT,
        pain_0_to_10=1,
        pupils=Pupils(True, True),
    )

    pcr = Pcr(
        pcr_id="pcr-x",
        event_name="Test",
        report_date=date(2026, 1, 2),
        report_time=time(10, 30),
        patient=patient,
        consent=ConsentStatus.GIVEN,
        history_description="Test",
        initial_vitals=[v0],
        treatments=[],
        disposition=None,
    )

    report = engine.evaluate(pcr)
    codes = {i.code for i in report.issues}
    assert "DISPOSITION_NOT_DOCUMENTED" in codes

