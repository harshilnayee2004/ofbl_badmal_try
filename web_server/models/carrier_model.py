import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Carrier(SQLModel, table=True):
    __tablename__ = "carriers"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    lot_id: Optional[int] = Field(default=None, foreign_key="lots.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    carrier_type: Optional[str] = Field(default="Carrier 6A/L")
    sequence_number: Optional[int] = Field(default=None)
    carrier_number: Optional[int] = Field(default=None)
    files_path: Optional[str] = Field(default=None)
    carrier_6al_inspection_id: Optional[int] = Field(default=None, foreign_key="carrier_6al_inspections.id")

    acceptance_status: Optional[bool] = Field(default=None)
    carrier_inspection_status: str = Field(default="Pending")

    start_time: Optional[datetime.datetime] = Field(default=None)
    end_time: Optional[datetime.datetime] = Field(default=None)
