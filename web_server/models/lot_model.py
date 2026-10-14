import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

class Lot(SQLModel, table=True):
    __tablename__ = "lots"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    lot_number: Optional[str] = Field(default=None)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    inspection_status: str = Field(default="Pending")
    box_inspection_status: str = Field(default="Pending")
    primer_inspection_status: str = Field(default="Pending")
    files_path: str=Field(default=None)

    number_of_carrier: Optional[int] = Field(default=None)
    number_of_carrier_to_inspect: Optional[int] = Field(default=None)
    carrier_type: Optional[str] = Field(default=None)
    carrier_current_sequence: Optional[int] = Field(default=1)
    carrier_count_confirmation: Optional[int] = Field(default=0)
    carrier_inspection_status: str = Field(default="Pending")
    carrier_acceptance_status: str = Field(default="Pending")

    number_of_box: Optional[int] = Field(default=None)
    number_of_primer: Optional[int] = Field(default=None)
    number_of_box_to_inspect: Optional[int] = Field(default=None)
    number_of_primer_to_inspect: Optional[int] = Field(default=None)
    box_type: Optional[str] = Field(default=None)
    # container_type: Optional[str] = Field(default=None) // are anything thhere called containers? cuz I am seeing carriers and containers both in this file
    primer_type: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    total_quantity: Optional[int] = Field(default=None)
    sampling_plan: Optional[str] = Field(default=None)

    box_current_sequence: Optional[int] = Field(default=None)
    primer_current_sequence: Optional[int] = Field(default=None)

    box_count_confirmation: Optional[int] = Field(default=0)
    primer_count_confirmation: Optional[int] = Field(default=0)

    box_acceptance_status: str = Field(default="Pending")
    primer_acceptance_status: str = Field(default="Pending")
    acceptance_status: str = Field(default="Pending")

    start_time: Optional[datetime.datetime] = Field(default=None)
    end_time: Optional[datetime.datetime] = Field(default=None)