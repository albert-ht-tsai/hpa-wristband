from datetime import date

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.core.logging import logger
from src.map.map_client import GoogleMapClient
from src.user.models.user_model import User
from src.user_device.models.user_device_model import UserDevice, UserDeviceHealthRecord, UserDeviceLocation
from src.user_device.schemas.user_device_schema import (
    BatchStatusResponse,
    DateListResponse,
    HealthRecordCreateRequest,
    HealthRecordResponse,
    LocationBatchCreateRequest,
    MonthDays,
    UserDeviceCreateRequest,
    UserDeviceUpdateRequest,
    YearMonths,
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
                start_date=data.start_date,
                end_date=data.end_date,
                latitude=point.lat,
                longitude=point.lng,
                timestamp=point.timestamp,
                address=address,
            )
        )

    db.add_all(db_locations)
    db.commit()
    return BatchStatusResponse(
        id=0,
        start_date=data.start_date,
        end_date=data.end_date,
        isLoading=False,
        isComplete=True,
        progress=1.0,
        error=None,
    )


def get_location_batch(
    db: Session, user: User, user_device_id: int, start_date: date, end_date: date
) -> list[UserDeviceLocation]:
    _get_owned_device(db, user, user_device_id)
    return (
        db.query(UserDeviceLocation)
        .filter(
            UserDeviceLocation.user_device_id == user_device_id,
            UserDeviceLocation.start_date >= start_date,
            UserDeviceLocation.start_date <= end_date,
        )
        .order_by(UserDeviceLocation.start_date.asc(), UserDeviceLocation.timestamp.asc())
        .all()
    )


def create_health_record(
    db: Session, user: User, user_device_id: int, data: HealthRecordCreateRequest
) -> UserDeviceHealthRecord:
    _get_owned_device(db, user, user_device_id)
    record = UserDeviceHealthRecord(
        user_device_id=user_device_id,
        start_date=data.start_date,
        end_date=data.end_date,
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
    db: Session, user: User, user_device_id: int, start_date: date, end_date: date
) -> list[UserDeviceHealthRecord]:
    _get_owned_device(db, user, user_device_id)
    return (
        db.query(UserDeviceHealthRecord)
        .filter(
            UserDeviceHealthRecord.user_device_id == user_device_id,
            UserDeviceHealthRecord.start_date >= start_date,
            UserDeviceHealthRecord.start_date <= end_date,
        )
        .order_by(UserDeviceHealthRecord.start_date.asc())
        .all()
    )


def health_record_to_status(record: UserDeviceHealthRecord) -> BatchStatusResponse:
    return BatchStatusResponse(
        id=record.id,
        start_date=record.start_date,
        end_date=record.end_date,
        isLoading=record.is_loading,
        isComplete=record.is_complete,
        progress=record.progress,
        error=record.error,
    )


def _dates_to_response(dates: list) -> DateListResponse:
    year_map: dict[int, dict[int, list[int]]] = {}
    for d in dates:
        if d is None:
            continue
        year_map.setdefault(d.year, {}).setdefault(d.month, []).append(d.day)
    return DateListResponse(
        data=[
            YearMonths(
                year=y,
                months=[
                    MonthDays(month=m, days=sorted(days))
                    for m, days in sorted(months.items())
                ],
            )
            for y, months in sorted(year_map.items())
        ]
    )


def get_location_dates(db: Session, user: User, user_device_id: int) -> DateListResponse:
    _get_owned_device(db, user, user_device_id)
    rows = (
        db.query(UserDeviceLocation.start_date)
        .filter(
            UserDeviceLocation.user_device_id == user_device_id,
            UserDeviceLocation.start_date.isnot(None),
        )
        .distinct()
        .order_by(UserDeviceLocation.start_date.asc())
        .all()
    )
    return _dates_to_response([r.start_date for r in rows])


def get_health_dates(db: Session, user: User, user_device_id: int) -> DateListResponse:
    _get_owned_device(db, user, user_device_id)
    rows = (
        db.query(UserDeviceHealthRecord.start_date)
        .filter(
            UserDeviceHealthRecord.user_device_id == user_device_id,
            UserDeviceHealthRecord.start_date.isnot(None),
        )
        .distinct()
        .order_by(UserDeviceHealthRecord.start_date.asc())
        .all()
    )
    return _dates_to_response([r.start_date for r in rows])


def health_record_to_response(record: UserDeviceHealthRecord) -> HealthRecordResponse:
    return HealthRecordResponse(
        id=record.id,
        start_date=record.start_date,
        end_date=record.end_date,
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
