from pydantic import BaseModel
from typing import Optional, Any

class PrimerStartInspectionRequest(BaseModel):
    primer_id: int
    primer_type: str = "Primer Electric 1A/L"
    lot_id: int

class PrimerStatusUpdateRequest(BaseModel):
    primer_id: int
    status: str

class PrimerParameterUpdateRequest(BaseModel):
    primer_id: int
    parameter_key: str
    value: bool

class PrimerNumberUpdateRequest(BaseModel):
    primer_id: int
    new_primer_number: str

class PrimerUpdateBoxRequest(BaseModel):
    primer_id: int
    box_id: int

class PrimerResponse(BaseModel):
    primer_id: int
    primer_sequence: int
    primer_type: str
    primer_inspection_status: str
    inspection: Optional[Any] = None

class PrimerAcceptanceStatusRequest(BaseModel):
    primer_id: int
    acceptance_status: bool

# Aliases for backward compatibility
FuzeStartInspectionRequest = PrimerStartInspectionRequest
FuzeStatusUpdateRequest = PrimerStatusUpdateRequest
FuzeParameterUpdateRequest = PrimerParameterUpdateRequest
FuzeNumberUpdateRequest = PrimerNumberUpdateRequest
FuzeUpdateBoxRequest = PrimerUpdateBoxRequest
FuzeResponse = PrimerResponse
FuzeAcceptanceStatusRequest = PrimerAcceptanceStatusRequest
