from pydantic import BaseModel


class SignupRequest(BaseModel):
    email: str
    password: str
    code: str


class SignupResponse(BaseModel):
    code: int
    msg: str


class VerificationCodeRequest(BaseModel):
    email: str


class VerificationCodeResponse(BaseModel):
    msg: str
    exp_minute: int


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    access_token_exp_minute: int
    refresh_token: str
    refresh_token_exp_day: int


class LogoutResponse(BaseModel):
    code: int
    msg: str
