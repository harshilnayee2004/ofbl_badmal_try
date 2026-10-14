import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Box(SQLModel, table=True):
    __tablename__ = "boxes"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    lot_id: Optional[int] = Field(default=None, foreign_key="lots.id")
    carrier_id: Optional[int] = Field(default=None, foreign_key="carriers.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    box_type: Optional[str] = Field(default=None)
    sequence_number: Optional[int] = Field(default=None)
    files_path: Optional[str] = Field(default=None)
    box_h2a_inspection_id: Optional[int] = Field(default=None, foreign_key="box_h2a_inspections.id")

    box_number: Optional[int] = Field(default=None)
    acceptance_status: Optional[bool] = Field(default=None)

    box_inspection_status: str = Field(default="Pending")

    start_time: Optional[datetime.datetime] = Field(default=None)
    end_time: Optional[datetime.datetime] = Field(default=None)


