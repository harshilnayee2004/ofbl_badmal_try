from sqlmodel import Session, select
from models.primer_model import Primer, Primer as Fuze
from models.primer_1al_inspection_model import Primer1ALInspection
from services.log_service import PrimerLogService, PrimerLogService as FuzeLogService
from socket_controller.primer_inspection_socket_controller import inspection_primer_manager, inspection_primer_manager as inspection_fuze_manager
from repositories.current_inspection_repositories import Primer1ALInspectionRepository

class Primer1ALSequenceService:
    """
    Business Logic Sequence Service for Level 3 Ordnance Unit: Primer Electric 1A/L
    Evaluates 6 critical ammunition acceptance parameters:
      Seq 1 -> cleanliness_appearance (Param 14)
      Seq 2 -> lot_number_match (Param 15)
      Seq 3 -> magazine_crack_damage (Param 16)
      Seq 4 -> paper_liner_damage_spillage (Param 17)
      Seq 5 -> rubber_ring_assembly (Param 18)
      Seq 6 -> magazine_assembly (Param 19)
    """

    @staticmethod
    async def process_result(db: Session, sequence_number: int, fuze_id: int, result_dict: dict, log_service: FuzeLogService):
        fuze = db.exec(select(Fuze).where(Fuze.id == fuze_id)).first()
        if not fuze or not fuze.primer_1al_inspection_id:
            return

        inspection = db.exec(select(Primer1ALInspection).where(Primer1ALInspection.id == fuze.primer_1al_inspection_id)).first()
        if not inspection:
            return

        param_updated = None
        log_desc = None

        if sequence_number == 1:
            # Cleanliness & Surface Appearance (True = Clean/Pass, False = Stains/Oil/Fail)
            val = result_dict.get("CLEANLINESS_APPEARANCE", result_dict.get("cleanliness_appearance", True))
            inspection.cleanliness_appearance = bool(val)
            param_updated = "cleanliness_appearance"
            log_desc = f"Surface Cleanliness Check (Param 14): {'PASSED (Oil & Stain Free)' if inspection.cleanliness_appearance else 'FAILED (Oil/Foreign Stains Detected)'}"

        elif sequence_number == 2:
            # Laser Lot Number Micro-OCR Match (True = Match/Pass, False = Mismatch/Fail)
            val = result_dict.get("LOT_NUMBER_MATCH", result_dict.get("lot_number_match", True))
            inspection.lot_number_match = bool(val)
            param_updated = "lot_number_match"
            log_desc = f"Laser Engraved Lot Number Micro-OCR (Param 15): {'PASSED (Exact Batch Match)' if inspection.lot_number_match else 'FAILED (Lot Mismatch)'}"

        elif sequence_number == 3:
            # Magazine Head Cracks / Dents (False = No Defect/Pass, True = Cracks Found/Fail)
            val = result_dict.get("MAGAZINE_CRACK_DAMAGE", result_dict.get("magazine_crack_damage", False))
            inspection.magazine_crack_damage = bool(val)
            param_updated = "magazine_crack_damage"
            log_desc = f"Magazine Head Structural Check (Param 16): {'PASSED (Crack/Dent Free)' if not inspection.magazine_crack_damage else 'FAILED (Cracks/Dents Detected)'}"

        elif sequence_number == 4:
            # Paper Liner Intactness & Gunpowder Spillage (False = Intact/Pass, True = Spillage/Fail)
            val = result_dict.get("PAPER_LINER_DAMAGE_SPILLAGE", result_dict.get("paper_liner_damage_spillage", False))
            inspection.paper_liner_damage_spillage = bool(val)
            param_updated = "paper_liner_damage_spillage"
            log_desc = f"Paper Liner Intactness (Param 17): {'PASSED (Zero Gunpowder Leakage)' if not inspection.paper_liner_damage_spillage else 'FAILED (Paper Damaged / Powder Spillage)'}"

        elif sequence_number == 5:
            # Rubber O-Ring Assembly (True = Present & Seated/Pass, False = Missing/Defective/Fail)
            val = result_dict.get("RUBBER_RING_ASSEMBLY", result_dict.get("rubber_ring_assembly", True))
            inspection.rubber_ring_assembly = bool(val)
            param_updated = "rubber_ring_assembly"
            log_desc = f"Rubber Ring Seating Check (Param 18): {'PASSED (O-Ring Seated in Recess)' if inspection.rubber_ring_assembly else 'FAILED (Missing/Misplaced O-Ring)'}"

        elif sequence_number == 6:
            # Magazine Assembly Alignment & Thread Gap < 0.2mm (True = Pass, False = Fail)
            val = result_dict.get("MAGAZINE_ASSEMBLY", result_dict.get("magazine_assembly", True))
            inspection.magazine_assembly = bool(val)
            param_updated = "magazine_assembly"
            log_desc = f"Magazine Assembly Alignment (Param 19): {'PASSED (Thread Gap < 0.2mm Concentric)' if inspection.magazine_assembly else 'FAILED (Thread Gap >= 0.2mm / Tilt)'}"

        # Evaluate acceptance status:
        # Criteria: cleanliness_appearance == True, lot_number_match == True, magazine_crack_damage == False,
        # paper_liner_damage_spillage == False, rubber_ring_assembly == True, magazine_assembly == True
        params_evaluated = [
            inspection.cleanliness_appearance,
            inspection.lot_number_match,
            (not inspection.magazine_crack_damage) if inspection.magazine_crack_damage is not None else None,
            (not inspection.paper_liner_damage_spillage) if inspection.paper_liner_damage_spillage is not None else None,
            inspection.rubber_ring_assembly,
            inspection.magazine_assembly
        ]

        if False in params_evaluated:
            fuze.acceptance_status = False
        elif all(p is True for p in params_evaluated):
            fuze.acceptance_status = True
        else:
            fuze.acceptance_status = None

        if sequence_number == 6:
            fuze.fuze_inspection_status = "Completed"

        db.add(inspection)
        db.add(fuze)
        db.commit()
        db.refresh(inspection)
        db.refresh(fuze)

        # Store in Inspection State Repository
        Primer1ALInspectionRepository.inspection_results = {
            "cleanliness_appearance": inspection.cleanliness_appearance,
            "lot_number_match": inspection.lot_number_match,
            "magazine_crack_damage": inspection.magazine_crack_damage,
            "paper_liner_damage_spillage": inspection.paper_liner_damage_spillage,
            "rubber_ring_assembly": inspection.rubber_ring_assembly,
            "magazine_assembly": inspection.magazine_assembly,
            "acceptance_status": fuze.acceptance_status
        }

        # Add log
        if log_desc:
            await log_service.add_fuze_log(description=log_desc, fuze_id=fuze_id)

        # Broadcast live parameter update to WebSocket clients
        if param_updated:
            await inspection_fuze_manager.send_json({
                "type": "parameter_update",
                "object": {
                    "parameter_key": param_updated,
                    "value": getattr(inspection, param_updated),
                    "acceptance_status": fuze.acceptance_status
                }
            })
