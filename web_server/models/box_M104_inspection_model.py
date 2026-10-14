from typing import Optional
from sqlmodel import SQLModel, Field

class BoxM104Inspection(SQLModel, table=True):
    __tablename__ = "box_m104_inspections"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    stenciling_5_sides: Optional[bool] = Field(default=None)
    explosive_label: Optional[bool] = Field(default=None)
    wooden_sheet: Optional[bool] = Field(default=None)
    packing_slip: Optional[bool] = Field(default=None)
    cotton_sheet: Optional[bool] = Field(default=None)
    container_count_50: Optional[bool] = Field(default=None)
    safety_pin_presence: Optional[bool] = Field(default=None)
    seals: Optional[bool] = Field(default=None)
    interior_rust_peeling_paint: Optional[bool] = Field(default=None)
