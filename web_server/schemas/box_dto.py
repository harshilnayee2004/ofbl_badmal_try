from typing import Optional
from pydantic import BaseModel

class BoxStartInspectionRequest(BaseModel):
    box_type: str
    lot_id: int
    box_id: int
    suppress_cam_error: Optional[bool] = False

class BoxStatusUpdateRequest(BaseModel):
    box_id: int
    status: str

class BoxParameterUpdateRequest(BaseModel):
    box_id: int
    parameter_key: str
    value: bool

class BoxNumberUpdateRequest(BaseModel):
    box_id: int
    lot_id: int
    new_box_number: int

class BoxAcceptanceStatusRequest(BaseModel):
    box_id: int
    acceptance_status: bool