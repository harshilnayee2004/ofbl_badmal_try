from pydantic import BaseModel

class InspectionDetailsRequestDTO(BaseModel):
    lot_id: int
    box_type: str