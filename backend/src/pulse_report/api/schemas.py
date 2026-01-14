from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field


class PupilsIn(BaseModel):
    left_reactive: bool
    right_reactive: bool


class VitalSignsIn(BaseModel):
    observed_at: datetime
    pulse_bpm: int
    resp_per_min: int
    systolic_bp: int
    diastolic_bp: int
    skin: str
    loc: str
    pain_0_to_10: int = Field(ge=0, le=10)
    pupils: PupilsIn


class TreatmentEntryIn(BaseModel):
    performed_at: datetime
    intervention: str
    results_notes: str = ""


class DispositionIn(BaseModel):
    discharge_time: time
    disposition: str
    accompanied_by: str
    discharge_instructions: str = ""


class PatientInfoIn(BaseModel):
    full_name: str
    date_of_birth: date
    sex: str = "Unknown"
    phone: str = ""
    allergies: str = ""
    medications: str = ""
    past_medical_history: str = ""


class CreatePcrRequest(BaseModel):
    event_name: str
    report_date: date
    report_time: time
    patient: PatientInfoIn
    consent: str
    history_description: str
    initial_vitals: list[VitalSignsIn]
    treatments: list[TreatmentEntryIn] = []
    disposition: Optional[DispositionIn] = None


class CreatePcrResponse(BaseModel):
    pcr_id: str


class PupilsOut(BaseModel):
    left_reactive: bool
    right_reactive: bool


class VitalSignsOut(BaseModel):
    observed_at: datetime
    pulse_bpm: int
    resp_per_min: int
    systolic_bp: int
    diastolic_bp: int
    skin: str
    loc: str
    pain_0_to_10: int
    pupils: PupilsOut


class TreatmentEntryOut(BaseModel):
    performed_at: datetime
    intervention: str
    results_notes: str


class DispositionOut(BaseModel):
    discharge_time: time
    disposition: str
    accompanied_by: str
    discharge_instructions: str


class PatientInfoOut(BaseModel):
    full_name: str
    date_of_birth: date
    sex: str
    phone: str
    allergies: str
    medications: str
    past_medical_history: str


class PcrResponse(BaseModel):
    pcr_id: str
    event_name: str
    report_date: date
    report_time: time
    patient: PatientInfoOut
    consent: str
    history_description: str
    initial_vitals: list[VitalSignsOut]
    treatments: list[TreatmentEntryOut]
    disposition: Optional[DispositionOut]


class QualityIssueOut(BaseModel):
    code: str
    message: str
    severity: str


class QualityReportResponse(BaseModel):
    pcr_id: str
    issue_count: int
    warning_count: int
    error_count: int
    issues: list[QualityIssueOut]


class UpdateDispositionRequest(BaseModel):
    discharge_time: Optional[time] = None
    disposition: Optional[str] = None
    accompanied_by: Optional[str] = None
    discharge_instructions: Optional[str] = None

