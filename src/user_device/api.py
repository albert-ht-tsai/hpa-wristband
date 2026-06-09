from datetime import date

from fastapi import APIRouter

from src.core.deps import CurrentUser, SessionDep
from src.user_device.schemas.user_device_schema import (
    HealthRecordCreateRequest,
    HealthRecordListResponse,
    HealthRecordResponse,
    LocationBatchCreateRequest,
    LocationBatchCreateResponse,
    LocationItem,
    LocationListResponse,
    UserDeviceCreateRequest,
    UserDeviceCreateResponse,
    UserDeviceDeleteResponse,
    UserDeviceListResponse,
    UserDeviceResponse,
    UserDeviceUpdateRequest,
    UserDeviceUpdateResponse,
)
from src.user_device.services.user_device_service import (
    create_device,
    create_health_record,
    create_location_batch,
    delete_device,
    get_devices,
    get_health_records,
    get_location_batch,
    health_record_to_response,
    update_device,
)

router = APIRouter(prefix="/users/devices", tags=["users_devices"])


@router.post("", response_model=UserDeviceCreateResponse, status_code=201)
def create_device_endpoint(body: UserDeviceCreateRequest, db: SessionDep, current_user: CurrentUser):
    device = create_device(db, current_user, body)
    return UserDeviceCreateResponse.model_validate(device)


@router.get("", response_model=UserDeviceListResponse)
def get_devices_endpoint(db: SessionDep, current_user: CurrentUser):
    devices = get_devices(db, current_user)
    return UserDeviceListResponse(
        data=[UserDeviceResponse.model_validate(d) for d in devices],
        count=len(devices),
    )


@router.put("/{user_device_id}", response_model=UserDeviceUpdateResponse)
def update_device_endpoint(user_device_id: int, body: UserDeviceUpdateRequest, db: SessionDep, current_user: CurrentUser):
    update_device(db, current_user, user_device_id, body)
    return UserDeviceUpdateResponse(code=201, msg="User device updated successfully")


@router.delete("/{user_device_id}", response_model=UserDeviceDeleteResponse)
def delete_device_endpoint(user_device_id: int, db: SessionDep, current_user: CurrentUser):
    delete_device(db, current_user, user_device_id)
    return UserDeviceDeleteResponse(code=204, msg="User device deleted successfully")


@router.post("/{user_device_id}/location-batch", response_model=LocationBatchCreateResponse, status_code=201)
def create_location_batch_endpoint(user_device_id: int, body: LocationBatchCreateRequest, db: SessionDep, current_user: CurrentUser):
    result = create_location_batch(db, current_user, user_device_id, body)
    return LocationBatchCreateResponse(
        code=201,
        msg="Location batch created successfully",
        total=result["total"],
        saved=result["saved"],
    )


@router.get("/{user_device_id}/location-batch", response_model=LocationListResponse)
def get_location_batch_endpoint(
    user_device_id: int,
    start_date: date,
    end_date: date,
    db: SessionDep,
    current_user: CurrentUser,
):
    locations = get_location_batch(db, current_user, user_device_id, start_date, end_date)
    return LocationListResponse(
        code=200,
        data=[LocationItem.model_validate(loc) for loc in locations],
        count=len(locations),
    )


@router.post("/{user_device_id}/health-batch", response_model=HealthRecordResponse, status_code=201)
def create_health_record_endpoint(user_device_id: int, body: HealthRecordCreateRequest, db: SessionDep, current_user: CurrentUser):
    record = create_health_record(db, current_user, user_device_id, body)
    return health_record_to_response(record)


@router.get("/{user_device_id}/health-batch", response_model=HealthRecordListResponse)
def get_health_records_endpoint(
    user_device_id: int,
    start_date: date,
    end_date: date,
    db: SessionDep,
    current_user: CurrentUser,
):
    records = get_health_records(db, current_user, user_device_id, start_date, end_date)
    return HealthRecordListResponse(
        data=[health_record_to_response(r) for r in records],
        count=len(records),
    )
