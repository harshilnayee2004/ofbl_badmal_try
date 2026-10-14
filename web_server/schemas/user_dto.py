from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str
    status: bool = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[bool] = None
    password: Optional[str] = None

class PasswordReset(BaseModel):
    new_password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    last_login: Optional[datetime]
    status: bool

    model_config = ConfigDict(from_attributes=True)
