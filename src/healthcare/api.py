from datetime import date

from fastapi import APIRouter

from src.core.deps import CurrentUser, SessionDep
from src.healthcare.schemas.healthcare_schema import (
    HealthcareReportListResponse,
    HealthcareReportResponse,
)
from src.healthcare.services.healthcare_service import (
    generate_healthcare_analysis,
    get_healthcare_reports,
    report_to_response,
)

router = APIRouter(prefix="/users/devices", tags=["healthcare"])


@router.get(
    "/{user_device_id}/healthcare/analysis",
    response_model=HealthcareReportResponse,
)
def get_analysis_endpoint(
    user_device_id: int,
    start_date: date,
    end_date: date,
    db: SessionDep,
    current_user: CurrentUser,
):
    return generate_healthcare_analysis(db, current_user, user_device_id, start_date, end_date)


@router.get(
    "/{user_device_id}/healthcare/reports",
    response_model=HealthcareReportListResponse,
)
def get_reports_endpoint(
    user_device_id: int,
    db: SessionDep,
    current_user: CurrentUser,
    start_date: date | None = None,
    end_date: date | None = None,
):
    reports = get_healthcare_reports(db, current_user, user_device_id, start_date, end_date)
    return HealthcareReportListResponse(
        data=[report_to_response(r) for r in reports],
        count=len(reports),
    )
