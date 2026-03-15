from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response

from pulse_report.app.repository import InMemoryPcrRepository, PcrRepository
from pulse_report.app.service import PcrService
from pulse_report.app.quality_service import QualityService
from pulse_report.domain.errors import DomainValidationError
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

from .schemas import (
    CreatePcrRequest,
    CreatePcrResponse,
    PcrResponse,
    QualityReportResponse,
    UpdateDispositionRequest,
    PcrListResponse,
    VitalSignsIn,
    TreatmentEntryIn,
)

def create_app(repo: PcrRepository | None = None) -> FastAPI:
    """
    App Factory (design pattern):
    - allows tests to inject a repo
    - allows prod to wire a different repo later (Postgres)
    """
    app = FastAPI(title="Pulse Report API", version="0.1.0")
    repository = repo or InMemoryPcrRepository()

    def get_service() -> PcrService:
        # Dependency Injection (FastAPI Depends)
        return PcrService(repo=repository)

    def get_quality_service() -> QualityService:
        return QualityService.default(repo=repository)

    @app.post("/pcr", status_code=201, response_model=CreatePcrResponse)
    def create_pcr(req: CreatePcrRequest, svc: PcrService = Depends(get_service)) -> CreatePcrResponse:
        try:
            pcr_id = svc.create_pcr(
                event_name=req.event_name,
                report_date=req.report_date,
                report_time=req.report_time,
                patient=_to_domain_patient(req.patient),
                consent=_to_domain_consent(req.consent),
                history_description=req.history_description,
                initial_vitals=[_to_domain_vitals(v) for v in req.initial_vitals],
                treatments=[_to_domain_treatment(t) for t in req.treatments],
                disposition=_to_domain_disposition(req.disposition),
            )
            return CreatePcrResponse(pcr_id=pcr_id)
        except (DomainValidationError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.get("/pcr", response_model=PcrListResponse)
    def list_pcrs(limit: int = 50, offset: int = 0, svc: PcrService = Depends(get_service)) -> PcrListResponse:
        try:
            pcrs = svc.list_pcrs(limit=limit, offset=offset)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        return PcrListResponse(
            items=[
                {
                    "pcr_id": p.pcr_id,
                    "event_name": p.event_name,
                    "report_date": p.report_date,
                    "report_time": p.report_time,
                    "patient_full_name": p.patient.full_name,
                    "consent": p.consent.value,
                    "has_disposition": p.disposition is not None,
                }
                for p in pcrs
            ]
        )

    @app.get("/pcr/{pcr_id}", response_model=PcrResponse)
    def get_pcr(pcr_id: str, svc: PcrService = Depends(get_service)) -> PcrResponse:
        pcr = svc.repo.get(pcr_id)
        if pcr is None:
            raise HTTPException(status_code=404, detail="PCR not found")
        return _to_api_pcr(pcr)

    @app.get("/pcr/{pcr_id}/summary")
    def get_summary(pcr_id: str, svc: PcrService = Depends(get_service)) -> Response:
        try:
            summary = svc.export_summary(pcr_id)
            return Response(content=summary, media_type="text/plain")
        except KeyError as e:
            raise HTTPException(status_code=404, detail="PCR not found") from e

    @app.get("/pcr/{pcr_id}/quality", response_model=QualityReportResponse)
    def get_quality(pcr_id: str, qs: QualityService = Depends(get_quality_service)) -> QualityReportResponse:
        try:
            report = qs.evaluate(pcr_id)
            return QualityReportResponse(
                pcr_id=pcr_id,
                issue_count=report.issue_count,
                warning_count=report.warning_count,
                error_count=report.error_count,
                issues=[
                    {"code": i.code, "message": i.message, "severity": i.severity.value}
                    for i in report.issues
                ],
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail="PCR not found") from e

    @app.patch("/pcr/{pcr_id}/disposition", response_model=PcrResponse)
    def patch_disposition(
        pcr_id: str,
        req: UpdateDispositionRequest,
        svc: PcrService = Depends(get_service),
    ) -> PcrResponse:
        try:
            updated = svc.update_disposition(
                pcr_id,
                discharge_time=req.discharge_time,
                disposition=req.disposition,
                accompanied_by=AccompaniedBy(req.accompanied_by) if req.accompanied_by is not None else None,
                discharge_instructions=req.discharge_instructions,
            )
            return _to_api_pcr(updated)
        except KeyError as e:
            raise HTTPException(status_code=404, detail="PCR not found") from e
        except (DomainValidationError, ValueError) as e:
            # ValueError covers invalid enum strings, etc.
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post("/pcr/{pcr_id}/vitals", response_model=PcrResponse)
    def add_vitals(
        pcr_id: str,
        req: VitalSignsIn,
        svc: PcrService = Depends(get_service),
    ) -> PcrResponse:
        try:
            vital = _to_domain_vitals(req)
            updated = svc.add_vital(pcr_id, vital)
            return _to_api_pcr(updated)
        except KeyError as e:
            raise HTTPException(status_code=404, detail="PCR not found") from e
        except (DomainValidationError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post("/pcr/{pcr_id}/treatments", response_model=PcrResponse)
    def add_treatments(
        pcr_id: str,
        req: TreatmentEntryIn,
        svc: PcrService = Depends(get_service),
    ) -> PcrResponse:
        try:
            treatment = _to_domain_treatment(req)
            updated = svc.add_treatment(pcr_id, treatment)
            return _to_api_pcr(updated)
        except KeyError as e:
            raise HTTPException(status_code=404, detail="PCR not found") from e
        except (DomainValidationError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    return app


# Optional convenience for running:
app = create_app()


def _to_domain_patient(p) -> PatientInfo:
    return PatientInfo(
        full_name=p.full_name,
        date_of_birth=p.date_of_birth,
        sex=Sex(p.sex),
        phone=p.phone,
        allergies=p.allergies,
        medications=p.medications,
        past_medical_history=p.past_medical_history,
    )


def _to_domain_consent(consent: str) -> ConsentStatus:
    return ConsentStatus(consent)


def _to_domain_vitals(v) -> VitalSigns:
    return VitalSigns(
        observed_at=v.observed_at,
        pulse_bpm=v.pulse_bpm,
        resp_per_min=v.resp_per_min,
        systolic_bp=v.systolic_bp,
        diastolic_bp=v.diastolic_bp,
        skin=v.skin,
        loc=LocLevel(v.loc),
        pain_0_to_10=v.pain_0_to_10,
        pupils=Pupils(left_reactive=v.pupils.left_reactive, right_reactive=v.pupils.right_reactive),
    )


def _to_domain_treatment(t) -> TreatmentEntry:
    return TreatmentEntry(
        performed_at=t.performed_at,
        intervention=t.intervention,
        results_notes=t.results_notes,
    )


def _to_domain_disposition(d) -> Disposition | None:
    if d is None:
        return None
    return Disposition(
        discharge_time=d.discharge_time,
        disposition=d.disposition,
        accompanied_by=AccompaniedBy(d.accompanied_by),
        discharge_instructions=d.discharge_instructions,
    )


def _to_api_pcr(pcr) -> PcrResponse:
    # Serialize domain -> API shape (simple manual mapping)
    return PcrResponse(
        pcr_id=pcr.pcr_id,
        event_name=pcr.event_name,
        report_date=pcr.report_date,
        report_time=pcr.report_time,
        patient={
            "full_name": pcr.patient.full_name,
            "date_of_birth": pcr.patient.date_of_birth,
            "sex": pcr.patient.sex.value,
            "phone": pcr.patient.phone,
            "allergies": pcr.patient.allergies,
            "medications": pcr.patient.medications,
            "past_medical_history": pcr.patient.past_medical_history,
        },
        consent=pcr.consent.value,
        history_description=pcr.history_description,
        initial_vitals=[
            {
                "observed_at": v.observed_at,
                "pulse_bpm": v.pulse_bpm,
                "resp_per_min": v.resp_per_min,
                "systolic_bp": v.systolic_bp,
                "diastolic_bp": v.diastolic_bp,
                "skin": v.skin,
                "loc": v.loc.value,
                "pain_0_to_10": v.pain_0_to_10,
                "pupils": {"left_reactive": v.pupils.left_reactive, "right_reactive": v.pupils.right_reactive},
            }
            for v in pcr.initial_vitals
        ],
        treatments=[
            {
                "performed_at": t.performed_at,
                "intervention": t.intervention,
                "results_notes": t.results_notes,
            }
            for t in pcr.treatments
        ],
        disposition=None
        if pcr.disposition is None
        else {
            "discharge_time": pcr.disposition.discharge_time,
            "disposition": pcr.disposition.disposition,
            "accompanied_by": pcr.disposition.accompanied_by.value,
            "discharge_instructions": pcr.disposition.discharge_instructions,
        },
    )

