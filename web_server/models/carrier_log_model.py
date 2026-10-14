import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class CarrierLog(SQLModel, table=True):
    __tablename__ = "carrier_logs"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    carrier_id: Optional[int] = Field(default=None, foreign_key="carriers.id")
    description: Optional[str] = Field(default=None)
    date_time: datetime.datetime = Field(default_factory=datetime.datetime.now)
