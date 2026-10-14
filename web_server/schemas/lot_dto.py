from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LotCreate(BaseModel):
    lot_number: str
    fuze_type: Optional[str] = "Primer Electric 1A/L"
    total_quantity: Optional[int] = None
    number_of_carrier: Optional[int] = None
    number_of_carrier_to_inspect: Optional[int] = 20
    number_of_box: Optional[int] = None
    number_of_box_to_inspect: Optional[int] = 60
    number_of_fuze: Optional[int] = None
    number_of_fuze_to_inspect: Optional[int] = 315
    carrier_type: Optional[str] = "Carrier 6A/L"
    box_type: Optional[str] = "H2A"

class LotResponse(BaseModel):
    id: int
    lot_number: str
    fuze_type: str
    acceptance_status: str
    inspection_status: str
    total_quantity: Optional[int] = None
    number_of_carrier: Optional[int] = None
    number_of_carrier_to_inspect: Optional[int] = None
    carrier_type: Optional[str] = None
    carrier_acceptance_status: Optional[str] = "Pending"
    number_of_box: Optional[int] = None
    number_of_box_to_inspect: Optional[int] = None
    box_type: Optional[str] = None
    box_acceptance_status: Optional[str] = "Pending"
    number_of_fuze: Optional[int] = None
    number_of_fuze_to_inspect: Optional[int] = None
    fuze_acceptance_status: Optional[str] = "Pending"
    created_at: datetime

    class Config:
        from_attributes = True

