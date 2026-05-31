from typing import Optional

from pydantic import BaseModel


class UserProfileRequest(BaseModel):
    name: Optional[str] = None
    sex: Optional[str] = None
    height: Optional[float] = None
    height_type: Optional[str] = None
    weight: Optional[float] = None
    weight_type: Optional[str] = None
    age: Optional[int] = None
    step_aim: Optional[float] = None
    step_aim_type: Optional[str] = None
    sleep_aim: Optional[float] = None
    sleep_aim_type: Optional[str] = None


class UserProfileResponse(BaseModel):
    name: Optional[str] = None
    sex: Optional[str] = None
    height: Optional[float] = None
    height_type: Optional[str] = None
    weight: Optional[float] = None
    weight_type: Optional[str] = None
    age: Optional[int] = None
    step_aim: Optional[float] = None
    step_aim_type: Optional[str] = None
    sleep_aim: Optional[float] = None
    sleep_aim_type: Optional[str] = None

    model_config = {"from_attributes": True}


class UpdateUserResponse(BaseModel):
    code: int
    msg: str
