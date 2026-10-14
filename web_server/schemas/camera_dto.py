from pydantic import BaseModel
from typing import Optional

class CameraBase(BaseModel):
    position: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None

class CameraUpdate(BaseModel):
    ip_address: str
    port: int
    username: str
    password: str

class CameraPreviewRequest(BaseModel):
    ip_address: str
    port: int
    username: str
    password: str

class CameraResponse(CameraBase):
    id: int

    class Config:
        from_attributes = True
