from fastapi import APIRouter

from src.core.deps import CurrentUser, SessionDep
from src.user_device.schemas.user_device_schema import (
    DailyHealthCreateRequest,
    DailyHealthCreateResponse,
    LocationCreateRequest,
    LocationCreateResponse,
    LocationItem,
    LocationListResponse,
    UserDeviceCreateRequest,
    UserDeviceCreateResponse,
    UserDeviceDeleteResponse,
    UserDeviceResponse,
    UserDeviceUpdateRequest,
    UserDeviceUpdateResponse,
)
from src.user_device.services.user_device_service import (
    create_device,
    create_health_batch,
    create_location,
    delete_device,
    get_device,
    get_locations,
    update_device,
)

router = APIRouter(prefix="/users/devices", tags=["users_devices"])


@router.post("", response_model=UserDeviceCreateResponse, status_code=201)
def create_device_endpoint(body: UserDeviceCreateRequest, db: SessionDep, current_user: CurrentUser):
    device = create_device(db, current_user, body)
    return UserDeviceCreateResponse.model_validate(device)


@router.get("/{user_device_id}", response_model=UserDeviceResponse)
def get_device_endpoint(user_device_id: int, db: SessionDep, current_user: CurrentUser):
    device = get_device(db, current_user, user_device_id)
    return UserDeviceResponse.model_validate(device)


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


@router.post("/{user_device_id}/daily-health", response_model=DailyHealthCreateResponse)
def create_daily_health_endpoint(user_device_id: int, body: DailyHealthCreateRequest, db: SessionDep, current_user: CurrentUser):
    create_health_batch(db, current_user, user_device_id, body)
    return DailyHealthCreateResponse(code=200, msg="Health batch created successfully")
