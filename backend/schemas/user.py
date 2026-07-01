from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserRole = Literal["candidate", "recruiter", "hr", "admin"]
ManagerRole = Literal["recruiter", "hr", "admin"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = "candidate"


class UserRead(BaseModel):
    id: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ManagerBootstrapRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: ManagerRole
