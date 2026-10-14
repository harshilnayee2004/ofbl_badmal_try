from typing import Optional
from sqlmodel import SQLModel, Field

class BoxH2AInspection(SQLModel, table=True):
    """
    Inspection model for Level 2 Packaging: Box H2A
    Evaluates 8 critical ordnance acceptance parameters:
      6. stenciling_5_sides: 5-side OCR verification
      7. explosive_label: Hazard Class 1.4S explosive sticker presence
      8. wooden_sheet: Top wooden protective sheet presence
      9. packing_slip: White/Brown packing slip presence and readability
      10. cotton_sheet: Cotton cushioning sheet presence and dryness
      11. primer_quantity_count: 36/36 Primers counted in 6x6 grid
      12. wooden_sheet_18_holes: 2x 18-hole wooden separator trays present
      13. interior_rust_peeling_paint: Internal cavity rust and paint peeling free
    """
    __tablename__ = "box_h2a_inspections"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    # 8 Testing Parameters for Box H2A
    stenciling_5_sides: Optional[bool] = Field(default=None, description="Param 6: 5-side OCR verification")
    explosive_label: Optional[bool] = Field(default=None, description="Param 7: Explosive sticker present & aligned")
    wooden_sheet: Optional[bool] = Field(default=None, description="Param 8: Top wooden sheet presence")
    packing_slip: Optional[bool] = Field(default=None, description="Param 9: White/Brown packing slip presence")
    cotton_sheet: Optional[bool] = Field(default=None, description="Param 10: Cotton cushioning sheet presence")
    primer_quantity_count: Optional[bool] = Field(default=None, description="Param 11: 36/36 Primers counted in grid")
    wooden_sheet_18_holes: Optional[bool] = Field(default=None, description="Param 12: 2x 18-hole wooden separator trays")
    interior_rust_peeling_paint: Optional[bool] = Field(default=None, description="Param 13: Interior cavity rust & paint peeling")
