from pydantic import BaseModel
from typing import Optional, Any

class FuzeStartInspectionRequest(BaseModel):
    fuze_id: int
    fuze_type: str
    lot_id: int

class FuzeStatusUpdateRequest(BaseModel):
    fuze_id: int
    status: str

class FuzeParameterUpdateRequest(BaseModel):
    fuze_id: int
    parameter_key: str
    value: bool

class FuzeNumberUpdateRequest(BaseModel):
    fuze_id: int
    new_fuze_number: str

class FuzeUpdateBoxRequest(BaseModel):
    fuze_id: int
    box_id: int

class FuzeResponse(BaseModel):
    fuze_id: int
    fuze_sequence: int
    fuze_type: str
    fuze_inspection_status: str
    inspection: Optional[Any] = None

class FuzeAcceptanceStatusRequest(BaseModel):
    fuze_id: int
    acceptance_status: bool
