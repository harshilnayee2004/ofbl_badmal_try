from typing import Optional
from sqlmodel import SQLModel, Field

class Primer1ALInspection(SQLModel, table=True):
    """
    Inspection model for Level 3 Ordnance Unit: Primer Electric 1A/L
    Evaluates 6 critical ammunition acceptance parameters:
      14. cleanliness_appearance: Surface free of oil, dirt, stains, and foreign contaminants
      15. lot_number_match: Laser lot number micro-OCR match against parent batch
      16. magazine_crack_damage: Magazine head shell free of cracks, dents, and deformations
      17. paper_liner_damage_spillage: Paper liner intactness and zero gunpowder leakage
      18. rubber_ring_assembly: Rubber O-ring present and correctly seated in machined recess
      19. magazine_assembly: Magazine thread gap < 0.2mm and concentric assembly alignment
    """
    __tablename__ = "primer_1al_inspections"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    # 6 Testing Parameters for Primer Electric 1A/L Unit
    cleanliness_appearance: Optional[bool] = Field(default=None, description="Param 14: Surface cleanliness & foreign contaminants")
    lot_number_match: Optional[bool] = Field(default=None, description="Param 15: Laser lot number micro-OCR match")
    magazine_crack_damage: Optional[bool] = Field(default=None, description="Param 16: Magazine head cracks or surface damage")
    paper_liner_damage_spillage: Optional[bool] = Field(default=None, description="Param 17: Paper liner intactness & gunpowder leakage")
    rubber_ring_assembly: Optional[bool] = Field(default=None, description="Param 18: Rubber O-ring presence & seating in recess")
    magazine_assembly: Optional[bool] = Field(default=None, description="Param 19: Thread gap < 0.2mm & concentric assembly")

# Alias for compatibility with GAP_ANALYSIS nomenclature
PrimerElectric1ALInspection = Primer1ALInspection
