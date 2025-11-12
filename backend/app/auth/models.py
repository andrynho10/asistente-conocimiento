from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    token: str
    user_id: int
    role: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class ErrorResponse(BaseModel):
    error: dict

class ErrorDetail(BaseModel):
    code: str
    message: str

class SuccessResponse(BaseModel):
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"