from datetime import date, datetime, time, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.core.logging import logger
from src.map.map_client import GoogleMapClient
from src.user.models.user_model import User
from src.user_device.models.user_device_model import UserDevice, UserDeviceHealthBatch, UserDeviceHealthRecord, UserDeviceLocation
from src.user_device.schemas.user_device_schema import (
    DailyHealthCreateRequest,
    HealthRecordCreateRequest,
    HealthRecordResponse,
    LocationBatchCreateRequest,
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
    existing = db.query(UserDevice).filter(
        UserDevice.user_id == user.id,
        UserDevice.mac_address == data.mac_address,
    ).first()
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"code": 409, "message": "Device with this MAC address already exists for this user"},
        )
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


def get_devices(db: Session, user: User) -> list[UserDevice]:
    return db.query(UserDevice).filter(UserDevice.user_id == user.id).all()


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


def get_health_batches(db: Session, user: User, user_device_id: int) -> list[UserDeviceHealthBatch]:
    _get_owned_device(db, user, user_device_id)
    return (
        db.query(UserDeviceHealthBatch)
        .filter(UserDeviceHealthBatch.user_device_id == user_device_id)
        .order_by(UserDeviceHealthBatch.created_at.desc())
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


def create_location_batch(
    db: Session, user: User, user_device_id: int, data: LocationBatchCreateRequest
) -> dict:
    _get_owned_device(db, user, user_device_id)

    client = None
    try:
        client = GoogleMapClient()
    except Exception as e:
        logger.warning("GoogleMapClient init failed, skipping geocoding: %s", e)

    db_locations = []
    for point in data.locations:
        address = None
        if client:
            try:
                address = client.get_address(f"{point.lat},{point.lng}")
            except Exception as e:
                logger.warning("Reverse geocoding failed for (%s, %s): %s", point.lat, point.lng, e)
        db_locations.append(
            UserDeviceLocation(
                user_device_id=user_device_id,
                latitude=point.lat,
                longitude=point.lng,
                timestamp=point.timestamp,
                address=address,
            )
        )

    db.add_all(db_locations)
    db.commit()
    return {"total": len(data.locations), "saved": len(db_locations)}


def get_location_batch(
    db: Session, user: User, user_device_id: int, start_date: date, end_date: date
) -> list[UserDeviceLocation]:
    _get_owned_device(db, user, user_device_id)
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return (
        db.query(UserDeviceLocation)
        .filter(
            UserDeviceLocation.user_device_id == user_device_id,
            UserDeviceLocation.timestamp >= start_dt,
            UserDeviceLocation.timestamp <= end_dt,
        )
        .order_by(UserDeviceLocation.timestamp.asc())
        .all()
    )


def create_health_record(
    db: Session, user: User, user_device_id: int, data: HealthRecordCreateRequest
) -> UserDeviceHealthRecord:
    _get_owned_device(db, user, user_device_id)
    record = UserDeviceHealthRecord(
        user_device_id=user_device_id,
        batch_date=data.batchDate,
        batch_size=data.batch.batch_size,
        record_count=data.batch.record_count,
        is_loading=False,
        is_complete=True,
        progress=1.0,
        error=None,
        sleep_by_day=[item.model_dump() for item in data.sleepByDay] if data.sleepByDay else None,
        heart_rate=data.heartRate.model_dump() if data.heartRate else None,
        blood_pressure=data.bloodPressure.model_dump() if data.bloodPressure else None,
        blood_oxygen=data.bloodOxygen.model_dump() if data.bloodOxygen else None,
        body_temperature=data.bodyTemperature.model_dump() if data.bodyTemperature else None,
        calories=data.calories.model_dump() if data.calories else None,
        distance=data.distance.model_dump() if data.distance else None,
        met=data.met.model_dump() if data.met else None,
        stress=data.stress.model_dump() if data.stress else None,
        hrv=data.hrv.model_dump() if data.hrv else None,
        ecg=data.ecg.model_dump() if data.ecg else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_health_records(
    db: Session, user: User, user_device_id: int
) -> list[UserDeviceHealthRecord]:
    _get_owned_device(db, user, user_device_id)
    return (
        db.query(UserDeviceHealthRecord)
        .filter(UserDeviceHealthRecord.user_device_id == user_device_id)
        .order_by(UserDeviceHealthRecord.created_at.desc())
        .all()
    )


def health_record_to_response(record: UserDeviceHealthRecord) -> HealthRecordResponse:
    return HealthRecordResponse(
        id=record.id,
        batchDate=record.batch_date,
        isLoading=record.is_loading,
        isComplete=record.is_complete,
        progress=record.progress,
        error=record.error,
        sleepByDay=record.sleep_by_day,
        heartRate=record.heart_rate,
        bloodPressure=record.blood_pressure,
        bloodOxygen=record.blood_oxygen,
        bodyTemperature=record.body_temperature,
        calories=record.calories,
        distance=record.distance,
        met=record.met,
        stress=record.stress,
        hrv=record.hrv,
        ecg=record.ecg,
    )
