from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.core.logging import logger
from src.map.map_client import GoogleMapClient
from src.user.models.user_model import User
from src.user_device.models.user_device_model import UserDevice, UserDeviceHealthBatch, UserDeviceLocation
from src.user_device.schemas.user_device_schema import (
    DailyHealthCreateRequest,
    LocationCreateRequest,
    UserDeviceCreateRequest,
    UserDeviceUpdateRequest,
)


def _get_owned_device(db: Session, user: User, user_device_id: int) -> UserDevice:
    device = db.query(UserDevice).filter(
        UserDevice.id == user_device_id,
        UserDevice.user_id == user.id,
    ).first()
    if not device:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": 404, "message": "Device not found"},
        )
    return device


def create_device(db: Session, user: User, data: UserDeviceCreateRequest) -> UserDevice:
    device = UserDevice(
        user_id=user.id,
        mac_address=data.mac_address,
        type=data.type,
        name=data.name,
        is_shared=data.is_shared,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def get_device(db: Session, user: User, user_device_id: int) -> UserDevice:
    return _get_owned_device(db, user, user_device_id)


def update_device(db: Session, user: User, user_device_id: int, data: UserDeviceUpdateRequest) -> None:
    device = _get_owned_device(db, user, user_device_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    db.add(device)
    db.commit()


def delete_device(db: Session, user: User, user_device_id: int) -> None:
    device = _get_owned_device(db, user, user_device_id)
    db.delete(device)
    db.commit()


def create_location(db: Session, user: User, user_device_id: int, data: LocationCreateRequest) -> UserDeviceLocation:
    _get_owned_device(db, user, user_device_id)

    address = None
    try:
        client = GoogleMapClient()
        address = client.get_address(f"{data.latitude},{data.longitude}")
    except Exception as e:
        logger.warning("Reverse geocoding failed for (%s, %s): %s", data.latitude, data.longitude, e)

    location = UserDeviceLocation(
        user_device_id=user_device_id,
        latitude=data.latitude,
        longitude=data.longitude,
        timestamp=data.timestamp,
        address=address,
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def get_locations(db: Session, user: User, user_device_id: int) -> list[UserDeviceLocation]:
    _get_owned_device(db, user, user_device_id)
    return (
        db.query(UserDeviceLocation)
        .filter(UserDeviceLocation.user_device_id == user_device_id)
        .order_by(UserDeviceLocation.timestamp.desc())
        .all()
    )


def create_health_batch(db: Session, user: User, user_device_id: int, data: DailyHealthCreateRequest) -> None:
    _get_owned_device(db, user, user_device_id)
    batch = UserDeviceHealthBatch(
        user_device_id=user_device_id,
        batch_size=data.batch.batch_size,
        record_count=data.batch.record_count,
        sleep_data=data.payload.sleep_data,
        origin_data_3=data.payload.origin_data_3,
    )
    db.add(batch)
    db.commit()
