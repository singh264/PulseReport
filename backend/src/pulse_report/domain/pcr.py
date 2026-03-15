from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Optional

from .errors import DomainValidationError


class Sex(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class ConsentStatus(str, Enum):
    GIVEN = "Given"
    REFUSED = "Refused"


class LocLevel(str, Enum):
    ALERT = "Alert"
    VERBAL = "Verbal"
    PAIN = "Pain"
    UNRESPONSIVE = "Unresponsive"


class AccompaniedBy(str, Enum):
    SELF = "Self"
    FRIEND_OR_RELATIVE = "Friend/Relative"
    POLICE = "Police"
    AMBULANCE = "Ambulance"


@dataclass(frozen=True)
class Pupils:
    left_reactive: bool
    right_reactive: bool


@dataclass(frozen=True)
class PatientInfo:
    full_name: str
    date_of_birth: date
    sex: Sex = Sex.UNKNOWN
    phone: str = ""
    allergies: str = ""
    medications: str = ""
    past_medical_history: str = ""

    def __post_init__(self) -> None:
        if not self.full_name.strip():
            raise DomainValidationError("Patient full_name must not be empty.")
        if self.date_of_birth > date.today():
            raise DomainValidationError("date_of_birth cannot be in the future.")


@dataclass(frozen=True)
class VitalSigns:
    observed_at: datetime
    pulse_bpm: int
    resp_per_min: int
    systolic_bp: int
    diastolic_bp: int
    skin: str
    loc: LocLevel
    pain_0_to_10: int
    pupils: Pupils

    def __post_init__(self) -> None:
        if self.pulse_bpm <= 0:
            raise DomainValidationError("pulse_bpm must be > 0")
        if self.resp_per_min <= 0:
            raise DomainValidationError("resp_per_min must be > 0")
        if self.systolic_bp <= 0 or self.diastolic_bp <= 0:
            raise DomainValidationError("BP values must be > 0")
        if not (0 <= self.pain_0_to_10 <= 10):
            raise DomainValidationError("pain_0_to_10 must be between 0 and 10")


@dataclass(frozen=True)
class TreatmentEntry:
    performed_at: datetime
    intervention: str
    results_notes: str = ""

    def __post_init__(self) -> None:
        if not self.intervention.strip():
            raise DomainValidationError("intervention must not be empty")


@dataclass(frozen=True)
class Disposition:
    discharge_time: time
    disposition: str  # keep flexible for now (Back to Event/Home/Hospital/etc.)
    accompanied_by: AccompaniedBy
    discharge_instructions: str = ""


@dataclass
class Pcr:
    # Aggregate Root
    pcr_id: str
    event_name: str
    report_date: date
    report_time: time
    patient: PatientInfo
    consent: ConsentStatus
    history_description: str

    initial_vitals: list[VitalSigns] = field(default_factory=list)
    treatments: list[TreatmentEntry] = field(default_factory=list)
    disposition: Optional[Disposition] = None

    def __post_init__(self) -> None:
        if not self.pcr_id.strip():
            raise DomainValidationError("pcr_id must not be empty")
        if not self.event_name.strip():
            raise DomainValidationError("event_name must not be empty")
        if not self.history_description.strip():
            raise DomainValidationError("history_description must not be empty")
        if len(self.initial_vitals) == 0:
            raise DomainValidationError("At least one initial vital sign entry is required.")

    def update_disposition(
        self,
        *,
        discharge_time: time | None = None,
        disposition: str | None = None,
        accompanied_by: AccompaniedBy | None = None,
        discharge_instructions: str | None = None,
    ) -> None:
        # No-op guard
        if (
            discharge_time is None
            and disposition is None
            and accompanied_by is None
            and discharge_instructions is None
        ):
            raise DomainValidationError("No disposition fields provided to update.")

        if discharge_instructions is not None and not discharge_instructions.strip():
            raise DomainValidationError("discharge_instructions must not be empty when provided.")

        if self.disposition is None:
            # Creating a disposition requires the core fields
            if discharge_time is None or disposition is None or accompanied_by is None:
                raise DomainValidationError(
                    "Cannot set disposition without discharge_time, disposition, and accompanied_by."
                )
            self.disposition = Disposition(
                discharge_time=discharge_time,
                disposition=disposition,
                accompanied_by=accompanied_by,
                discharge_instructions=discharge_instructions or "",
            )
            return

        # Updating existing disposition: merge provided fields
        current = self.disposition
        self.disposition = Disposition(
            discharge_time=discharge_time or current.discharge_time,
            disposition=disposition or current.disposition,
            accompanied_by=accompanied_by or current.accompanied_by,
            discharge_instructions=(
                discharge_instructions if discharge_instructions is not None else current.discharge_instructions
            ),
        )

    def add_vital(self, vital: VitalSigns) -> None:
        if self.initial_vitals:
            latest = max(v.observed_at for v in self.initial_vitals)
            if vital.observed_at < latest:
                raise DomainValidationError("observed_at cannot be earlier than the latest recorded vitals timestamp.")

        self.initial_vitals.append(vital)
        # Keep stored vitals chronological for predictable reads
        self.initial_vitals.sort(key=lambda v: v.observed_at)

    def add_treatment(self, treatment: TreatmentEntry) -> None:
        self.treatments.append(treatment)
        # Keep stored treatments chronological for predictable reads
        self.treatments.sort(key=lambda t: t.performed_at)
