from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


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
