from pydantic import BaseModel
from typing import Optional, Any

class CarrierStartInspectionRequest(BaseModel):
    carrier_id: int
    carrier_type: Optional[str] = "Carrier 6A/L"
    lot_id: int

class CarrierStatusUpdateRequest(BaseModel):
    carrier_id: int
    status: str

class CarrierParameterUpdateRequest(BaseModel):
    carrier_id: int
    parameter_key: str
    value: bool

class CarrierNumberUpdateRequest(BaseModel):
    carrier_id: int
    lot_id: int
    new_carrier_number: int

class CarrierAcceptanceStatusRequest(BaseModel):
    carrier_id: int
    acceptance_status: bool

class CarrierResponse(BaseModel):
    carrier_id: int
    sequence_number: Optional[int] = None
    carrier_number: Optional[int] = None
    carrier_type: str = "Carrier 6A/L"
    carrier_inspection_status: str = "Pending"
    acceptance_status: Optional[bool] = None
    inspection: Optional[Any] = None
