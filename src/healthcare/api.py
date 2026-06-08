from fastapi import APIRouter

from src.core.deps import CurrentUser, SessionDep
from src.healthcare.schemas.healthcare_schema import (
    HealthcareAnalysisRequest,
    HealthcareReportListResponse,
    HealthcareReportResponse,
)
from src.healthcare.services.healthcare_service import (
    create_healthcare_analysis,
    get_healthcare_reports,
    report_to_response,
)

router = APIRouter(prefix="/users/devices", tags=["healthcare"])


@router.post(
    "/{user_device_id}/healthcare/analysis",
    response_model=HealthcareReportResponse,
    status_code=201,
)
def create_analysis_endpoint(
    user_device_id: int,
    body: HealthcareAnalysisRequest,
    db: SessionDep,
    current_user: CurrentUser,
):
    report = create_healthcare_analysis(db, current_user, user_device_id, body.health_record_id)
    return report_to_response(report)


@router.get(
    "/{user_device_id}/healthcare/reports",
    response_model=HealthcareReportListResponse,
)
def get_reports_endpoint(
    user_device_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    reports = get_healthcare_reports(db, current_user, user_device_id)
    return HealthcareReportListResponse(
        data=[report_to_response(r) for r in reports],
        count=len(reports),
    )
