from typing import Optional
from sqlmodel import SQLModel, Field

class Camera(SQLModel, table=True):
    __tablename__ = "cameras"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    position: Optional[str] = Field(default=None)
    feed_rotation: Optional[int] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    port: Optional[int] = Field(default=None)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    rtsp_url: Optional[str] = Field(default=None)
    streaming_status: Optional[bool] = Field(default=True)
