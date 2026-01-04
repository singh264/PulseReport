from datetime import date, datetime, time

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
    VitalSigns,
)


def main() -> None:
    repo = InMemoryPcrRepository()
    svc = PcrService(repo=repo)

    patient = PatientInfo(
        full_name="Demo Patient",
        date_of_birth=date(1999, 5, 1),
        sex=Sex.UNKNOWN,
        phone="555-111-2222",
        allergies="NKA",
        medications="None",
        past_medical_history="None",
    )

    vs = VitalSigns(
        observed_at=datetime(2026, 1, 2, 19, 10),
        pulse_bpm=88,
        resp_per_min=16,
        systolic_bp=118,
        diastolic_bp=76,
        skin="Warm",
        loc=LocLevel.ALERT,
        pain_0_to_10=1,
        pupils=Pupils(left_reactive=True, right_reactive=True),
    )

    pcr_id = svc.create_pcr(
        event_name="Demo Event",
        report_date=date(2026, 1, 2),
        report_time=time(19, 15),
        patient=patient,
        consent=ConsentStatus.GIVEN,
        history_description="Mild headache after prolonged standing.",
        initial_vitals=[vs],
        treatments=[],
        disposition=Disposition(
            discharge_time=time(19, 45),
            disposition="Home",
            accompanied_by=AccompaniedBy.FRIEND_OR_RELATIVE,
            discharge_instructions="Rest, hydrate, seek care if worse.",
        ),
    )

    print(svc.export_summary(pcr_id))


if __name__ == "__main__":
    main()

