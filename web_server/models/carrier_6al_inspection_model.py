from typing import Optional
from sqlmodel import SQLModel, Field

class Carrier6ALInspection(SQLModel, table=True):
    """
    Inspection model for Level 1 Packaging: Carrier 6A/L
    Evaluates 5 critical ordnance acceptance parameters:
      1. sealed_box: Wire/Lead seal presence and integrity
      2. damage_box: External cracks, dents, and punctures
      3. rusty_box: External rust and oxidation
      4. stenciling: OCR stenciling format validation
      5. explosive_label: Hazard Class 1.4S explosive sticker presence
    """
    __tablename__ = "carrier_6al_inspections"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    # 5 Testing Parameters for Carrier 6A/L
    sealed_box: Optional[bool] = Field(default=None, description="Param 1: Wire / Lead seal intact")
    damage_box: Optional[bool] = Field(default=None, description="Param 2: Dents, cracks, deformations")
    rusty_box: Optional[bool] = Field(default=None, description="Param 3: Rust / surface corrosion")
    stenciling: Optional[bool] = Field(default=None, description="Param 4: Stenciling OCR verification")
    explosive_label: Optional[bool] = Field(default=None, description="Param 5: Hazard Class 1.4S / Explosive sticker")
