import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Fuze(SQLModel, table=True):
    __tablename__ = "fuzes"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    lot_id: Optional[int] = Field(default=None, foreign_key="lots.id")
    box_id: Optional[int] = Field(default=None, foreign_key="boxes.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    fuze_type: Optional[str] = Field(default=None)
    sequence_number: Optional[int] = Field(default=None)
    files_path: Optional[str] = Field(default=None)
    fuze_number: Optional[int] = Field(default=None)
    acceptance_status: Optional[bool] = Field(default=None)
    fuze_inspection_status: str = Field(default="Pending")
    primer_1al_inspection_id: Optional[int] = Field(default=None, foreign_key="primer_1al_inspections.id")
    start_time: Optional[datetime.datetime] = Field(default=None)
    end_time: Optional[datetime.datetime] = Field(default=None)
