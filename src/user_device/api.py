from datetime import date

from fastapi import APIRouter

from src.core.deps import CurrentUser, SessionDep
from src.user_device.schemas.user_device_schema import (
    DailyHealthCreateRequest,
    DailyHealthCreateResponse,
    DailyHealthItem,
    DailyHealthListResponse,
    HealthRecordCreateRequest,
    HealthRecordListResponse,
    HealthRecordResponse,
    LocationCreateRequest,
    LocationCreateResponse,
    LocationItem,
    LocationListResponse,
    LocationBatchCreateRequest,
    LocationBatchCreateResponse,
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
    create_health_batch,
    create_health_record,
    create_location,
    create_location_batch,
    get_location_batch,
    delete_device,
    get_devices,
    get_health_batches,
    get_health_records,
    get_locations,
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


@router.post("/{user_device_id}/location", response_model=LocationCreateResponse)
def create_location_endpoint(user_device_id: int, body: LocationCreateRequest, db: SessionDep, current_user: CurrentUser):
    create_location(db, current_user, user_device_id, body)
    return LocationCreateResponse(code=200, msg="Location created successfully")


@router.get("/{user_device_id}/location", response_model=LocationListResponse)
def get_locations_endpoint(user_device_id: int, db: SessionDep, current_user: CurrentUser):
    locations = get_locations(db, current_user, user_device_id)
    return LocationListResponse(
        code=200,
        data=[LocationItem.model_validate(loc) for loc in locations],
        count=len(locations),
    )


@router.get("/{user_device_id}/daily-health", response_model=DailyHealthListResponse)
def get_daily_health_endpoint(user_device_id: int, db: SessionDep, current_user: CurrentUser):
    batches = get_health_batches(db, current_user, user_device_id)
    return DailyHealthListResponse(
        data=[DailyHealthItem.model_validate(b) for b in batches],
        count=len(batches),
    )


@router.post("/{user_device_id}/daily-health", response_model=DailyHealthCreateResponse)
def create_daily_health_endpoint(user_device_id: int, body: DailyHealthCreateRequest, db: SessionDep, current_user: CurrentUser):
    create_health_batch(db, current_user, user_device_id, body)
    return DailyHealthCreateResponse(code=200, msg="Health batch created successfully")


@router.post("/{user_device_id}/location-batch", response_model=LocationBatchCreateResponse, status_code=201)
def create_location_batch_endpoint(user_device_id: int, body: LocationBatchCreateRequest, db: SessionDep, current_user: CurrentUser):
    result = create_location_batch(db, current_user, user_device_id, body)
    return LocationBatchCreateResponse(
        code=201,
        msg="Location batch created successfully",
        total=result["total"],
        saved=result["saved"],
    )


@router.post("/{user_device_id}/health-batch", response_model=HealthRecordResponse, status_code=201)
def create_health_record_endpoint(user_device_id: int, body: HealthRecordCreateRequest, db: SessionDep, current_user: CurrentUser):
    record = create_health_record(db, current_user, user_device_id, body)
    return health_record_to_response(record)


@router.get("/{user_device_id}/health-batch", response_model=HealthRecordListResponse)
def get_health_records_endpoint(user_device_id: int, db: SessionDep, current_user: CurrentUser):
    records = get_health_records(db, current_user, user_device_id)
    return HealthRecordListResponse(
        data=[health_record_to_response(r) for r in records],
        count=len(records),
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
