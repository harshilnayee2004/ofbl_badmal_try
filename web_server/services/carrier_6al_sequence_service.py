from sqlmodel import Session, select
from models.carrier_model import Carrier
from models.carrier_6al_inspection_model import Carrier6ALInspection
from services.log_service import CarrierLogService
from socket_controller.carrier_inspection_socket_controller import inspection_carrier_manager
from repositories.current_inspection_repositories import CarrierInspectionRepository

class Carrier6ALSequenceService:
    """
    Business Logic Sequence Service for Level 1 Packaging: Carrier 6A/L
    Processes AI results across 5 inspection parameters:
      Seq 1 -> sealed_box (Param 1)
      Seq 2 -> damage_box (Param 2)
      Seq 3 -> rusty_box (Param 3)
      Seq 4 -> stenciling (Param 4)
      Seq 5 -> explosive_label (Param 5)
    """

    @staticmethod
    async def process_result(db: Session, sequence_number: int, carrier_id: int, result_dict: dict, log_service: CarrierLogService):
        carrier = db.exec(select(Carrier).where(Carrier.id == carrier_id)).first()
        if not carrier or not carrier.carrier_6al_inspection_id:
            return

        inspection = db.exec(select(Carrier6ALInspection).where(Carrier6ALInspection.id == carrier.carrier_6al_inspection_id)).first()
        if not inspection:
            return

        param_updated = None
        status_value = None
        log_desc = None

        if sequence_number == 1:
            # Wire/Lead Seal Check (True = Intact/Pass, False = Broken/Fail)
            val = result_dict.get("SEALED_BOX", result_dict.get("sealed_box", True))
            inspection.sealed_box = bool(val)
            param_updated = "sealed_box"
            status_value = inspection.sealed_box
            log_desc = f"Wire/Lead Seal Integrity Checked: {'PASSED' if inspection.sealed_box else 'FAILED (Broken/Missing)'}"

        elif sequence_number == 2:
            # Damage / Cracks / Dents (True = Defect/Fail, False = Clean/Pass)
            val = result_dict.get("DAMAGE_BOX", result_dict.get("damage_box", False))
            inspection.damage_box = bool(val)
            param_updated = "damage_box"
            status_value = not inspection.damage_box # For UI pass/fail display
            log_desc = f"Carrier Surface Physical Damage Checked: {'PASSED (No Dents)' if not inspection.damage_box else 'FAILED (Dents/Cracks Detected)'}"

        elif sequence_number == 3:
            # Rust / Oxidation (True = Rust Found/Fail, False = Clean/Pass)
            val = result_dict.get("RUSTY_BOX", result_dict.get("rusty_box", False))
            inspection.rusty_box = bool(val)
            param_updated = "rusty_box"
            status_value = not inspection.rusty_box
            log_desc = f"Carrier Rust & Oxidation Checked: {'PASSED (Rust Free)' if not inspection.rusty_box else 'FAILED (Corrosion Detected)'}"

        elif sequence_number == 4:
            # Stenciling OCR format (True = Matched/Pass, False = Mismatched/Fail)
            val = result_dict.get("CARRIER_STENCILING", result_dict.get("stenciling", True))
            inspection.stenciling = bool(val)
            param_updated = "stenciling"
            status_value = inspection.stenciling
            log_desc = f"Carrier Stenciling OCR Verification: {'PASSED' if inspection.stenciling else 'FAILED (OCR Mismatch)'}"

        elif sequence_number == 5:
            # Explosive Hazard Label (True = Present/Pass, False = Missing/Fail)
            val = result_dict.get("EXPLOSIVE_LABEL", result_dict.get("explosive_label", True))
            inspection.explosive_label = bool(val)
            param_updated = "explosive_label"
            status_value = inspection.explosive_label
            log_desc = f"Carrier Hazard Class 1.4S Label Check: {'PASSED' if inspection.explosive_label else 'FAILED (Missing/Damaged Label)'}"

        # Evaluate acceptance status:
        # Criteria: sealed_box == True, damage_box == False, rusty_box == False, stenciling == True, explosive_label == True
        params_evaluated = [
            inspection.sealed_box,
            (not inspection.damage_box) if inspection.damage_box is not None else None,
            (not inspection.rusty_box) if inspection.rusty_box is not None else None,
            inspection.stenciling,
            inspection.explosive_label
        ]

        if False in params_evaluated:
            carrier.acceptance_status = False
        elif all(p is True for p in params_evaluated):
            carrier.acceptance_status = True
        else:
            carrier.acceptance_status = None

        if sequence_number == 5:
            carrier.carrier_inspection_status = "Completed"

        db.add(inspection)
        db.add(carrier)
        db.commit()
        db.refresh(inspection)
        db.refresh(carrier)

        # Store in Inspection State Repository
        CarrierInspectionRepository.inspection_results = {
            "sealed_box": inspection.sealed_box,
            "damage_box": inspection.damage_box,
            "rusty_box": inspection.rusty_box,
            "stenciling": inspection.stenciling,
            "explosive_label": inspection.explosive_label,
            "acceptance_status": carrier.acceptance_status
        }

        # Add log
        if log_desc:
            await log_service.add_carrier_log(description=log_desc, carrier_id=carrier_id)

        # Send live parameter update to WebSocket clients
        if param_updated:
            await inspection_carrier_manager.send_json({
                "type": "parameter_update",
                "object": {
                    "parameter_key": param_updated,
                    "value": getattr(inspection, param_updated),
                    "acceptance_status": carrier.acceptance_status
                }
            })
