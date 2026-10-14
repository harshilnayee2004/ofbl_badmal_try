import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class BoxLog(SQLModel, table=True):
    __tablename__ = "box_logs"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    description: str = Field(default="")
    date_time: datetime.datetime = Field(default_factory=datetime.datetime.now)
    box_id: Optional[int] = Field(default=None, foreign_key="boxes.id")


