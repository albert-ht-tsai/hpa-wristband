from datetime import date, datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field


class UserDeviceCreateRequest(BaseModel):
    mac_address: str
    type: str
    name: str
    is_shared: bool = False


class UserDeviceUpdateRequest(BaseModel):
    name: Optional[str] = None
    is_shared: Optional[bool] = None


class UserDeviceResponse(BaseModel):
    id: int
    mac_address: str
    type: str
    name: str
    is_shared: bool

    model_config = {"from_attributes": True}


class UserDeviceListResponse(BaseModel):
    data: List[UserDeviceResponse]
    count: int


class UserDeviceCreateResponse(BaseModel):
    id: int
    mac_address: str
    type: str
    name: str
    is_shared: bool

    model_config = {"from_attributes": True}


class UserDeviceUpdateResponse(BaseModel):
    code: int
    msg: str


class UserDeviceDeleteResponse(BaseModel):
    code: int
    msg: str


class LocationCreateRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime


class LocationCreateResponse(BaseModel):
    code: int
    msg: str


class LocationItem(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    address: Optional[str] = None

    model_config = {"from_attributes": True}


class LocationListResponse(BaseModel):
    code: int
    data: List[LocationItem]
    count: int


class HealthBatchInfo(BaseModel):
    batch_size: int
    record_count: int


class HealthPayload(BaseModel):
    sleep_data: list = []
    origin_data_3: list = []


class DailyHealthCreateRequest(BaseModel):
    user_device_id: int
    batch: HealthBatchInfo
    payload: HealthPayload


class DailyHealthCreateResponse(BaseModel):
    code: int
    msg: str


class DailyHealthItem(BaseModel):
    id: int
    user_device_id: int
    batch_size: int
    record_count: int
    sleep_data: list
    origin_data_3: list
    created_at: datetime

    model_config = {"from_attributes": True}


class DailyHealthListResponse(BaseModel):
    data: List[DailyHealthItem]
    count: int


# ---- Health Record Schemas ----

class SleepDayItem(BaseModel):
    dayIndex: int
    totalMinutes: int
    deepMinutes: int
    lightMinutes: int
    wakeCount: int
    quality: int
    bedTimeMinutes: int
    wakeTimeMinutes: int
    sleepLine: str


class HeartRateSlot(BaseModel):
    timeMinutes: int
    bpm: int
    ecgCount: int
    ppgCount: int


class HeartRateData(BaseModel):
    slots: List[HeartRateSlot]


class BloodPressureSlot(BaseModel):
    timeMinutes: int
    systolic: int
    diastolic: int


class BloodPressureData(BaseModel):
    slots: List[BloodPressureSlot]


class BloodOxygenSlot(BaseModel):
    timeMinutes: int
    avgPct: int
    minPct: int
    maxPct: int


class BloodOxygenData(BaseModel):
    slots: List[BloodOxygenSlot]


class BodyTemperatureSlot(BaseModel):
    timeMinutes: int
    avgSkin: float
    avgBody: float


class BodyTemperatureData(BaseModel):
    slots: List[BodyTemperatureSlot]


class CaloriesSlot(BaseModel):
    timeMinutes: int
    kcal: float


class CaloriesData(BaseModel):
    totalKcal: float
    slots: List[CaloriesSlot]


class DistanceSlot(BaseModel):
    timeMinutes: int
    km: float


class DistanceData(BaseModel):
    totalKm: float
    slots: List[DistanceSlot]


class MetSlot(BaseModel):
    timeMinutes: int
    sportValue: int
    steps: int


class MetData(BaseModel):
    totalSteps: int
    slots: List[MetSlot]


class StressSlot(BaseModel):
    timeMinutes: int
    avgLoad: int


class StressData(BaseModel):
    slots: List[StressSlot]


class HrvSlot(BaseModel):
    timeMinutes: int
    value: float


class HrvData(BaseModel):
    slots: List[HrvSlot]


class EcgSlot(BaseModel):
    timeMinutes: int
    avgValue: float


class EcgData(BaseModel):
    slots: List[EcgSlot]


class HealthRecordCreateRequest(BaseModel):
    batch: HealthBatchInfo
    batchDate: date
    sleepByDay: Optional[List[SleepDayItem]] = None
    heartRate: Optional[HeartRateData] = None
    bloodPressure: Optional[BloodPressureData] = None
    bloodOxygen: Optional[BloodOxygenData] = None
    bodyTemperature: Optional[BodyTemperatureData] = None
    calories: Optional[CaloriesData] = None
    distance: Optional[DistanceData] = None
    met: Optional[MetData] = None
    stress: Optional[StressData] = None
    hrv: Optional[HrvData] = None
    ecg: Optional[EcgData] = None


class HealthRecordResponse(BaseModel):
    id: int
    batchDate: Optional[date] = None
    isLoading: bool
    isComplete: bool
    progress: float
    error: Optional[str] = None
    sleepByDay: Optional[list] = None
    heartRate: Optional[dict] = None
    bloodPressure: Optional[dict] = None
    bloodOxygen: Optional[dict] = None
    bodyTemperature: Optional[dict] = None
    calories: Optional[dict] = None
    distance: Optional[dict] = None
    met: Optional[dict] = None
    stress: Optional[dict] = None
    hrv: Optional[dict] = None
    ecg: Optional[dict] = None


class HealthRecordListResponse(BaseModel):
    data: List[HealthRecordResponse]
    count: int


# ---- Trajectory / Location Batch Schemas ----

class TrajectoryPoint(BaseModel):
    lat: float
    lng: float
    timestamp: datetime


class TrajectoryBatchInfo(BaseModel):
    batch_size: int
    record_count: int


class LocationBatchCreateRequest(BaseModel):
    batch: TrajectoryBatchInfo
    locations: Annotated[List[TrajectoryPoint], Field(max_length=50)]


class LocationBatchCreateResponse(BaseModel):
    code: int
    msg: str
    total: int
    saved: int
