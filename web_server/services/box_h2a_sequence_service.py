from sqlmodel import Session, select
from models.box_model import Box
from models.box_h2a_inspection_model import BoxH2AInspection
from services.log_service import BoxLogService
from socket_controller.box_inspection_socket_controller import inspection_box_manager
from repositories.current_inspection_repositories import BoxH2AInspectionRepository

class BoxH2ASequenceService:
    """
    Business Logic Sequence Service for Level 2 Packaging: Box H2A
    Evaluates 8 inspection parameters across 12 inspection sequences:
      Seq 1..5  -> stenciling_5_sides (Param 6)
      Seq 6     -> explosive_label (Param 7)
      Seq 7     -> wooden_sheet (Param 8)
      Seq 8     -> packing_slip (Param 9)
      Seq 9     -> cotton_sheet (Param 10)
      Seq 10    -> primer_quantity_count (Param 11)
      Seq 11    -> wooden_sheet_18_holes (Param 12)
      Seq 12    -> interior_rust_peeling_paint (Param 13)
    """

    @staticmethod
    async def process_result(db: Session, sequence_number: int, box_id: int, result_dict: dict, log_service: BoxLogService):
        box = db.exec(select(Box).where(Box.id == box_id)).first()
        if not box or not box.box_h2a_inspection_id:
            return

        inspection = db.exec(select(BoxH2AInspection).where(BoxH2AInspection.id == box.box_h2a_inspection_id)).first()
        if not inspection:
            return

        param_updated = None
        log_desc = None

        if 1 <= sequence_number <= 5:
            # 5-side OCR stenciling check
            side_val = result_dict.get(f"SIDE_{sequence_number}_STENCILING", result_dict.get("stenciling", True))
            side_pass = bool(side_val)
            
            # Store in repository dictionary
            BoxH2AInspectionRepository.stenciling_results[f"side_{sequence_number}"] = side_pass

            # If all 5 evaluated or sequence 5 reached, update inspection.stenciling_5_sides
            if sequence_number == 5:
                all_sides = [BoxH2AInspectionRepository.stenciling_results.get(f"side_{i}", True) for i in range(1, 6)]
                inspection.stenciling_5_sides = all(all_sides)
                param_updated = "stenciling_5_sides"
                log_desc = f"Box H2A 5-Side Stenciling OCR Evaluation: {'PASSED (5/5 Sides Matched)' if inspection.stenciling_5_sides else 'FAILED (OCR Mismatch)'}"
            else:
                log_desc = f"Box H2A Side #{sequence_number} OCR Verified: {'MATCHED' if side_pass else 'MISMATCH'}"

        elif sequence_number == 6:
            # Explosive Label (Class 1.4S sticker present on box)
            val = result_dict.get("EXPLOSIVE_LABEL", result_dict.get("explosive_label", True))
            inspection.explosive_label = bool(val)
            param_updated = "explosive_label"
            log_desc = f"Box Explosive Hazard Label Check: {'PASSED' if inspection.explosive_label else 'FAILED (Missing/Damaged Sticker)'}"

        elif sequence_number == 7:
            # Top Wooden Sheet (Protective Cover)
            val = result_dict.get("WOODEN_SHEET", result_dict.get("wooden_sheet", True))
            inspection.wooden_sheet = bool(val)
            param_updated = "wooden_sheet"
            log_desc = f"Top Wooden Protective Sheet Check: {'PASSED (Present)' if inspection.wooden_sheet else 'FAILED (Missing Sheet)'}"

        elif sequence_number == 8:
            # Packing Slip (White/Brown slip present and valid)
            val = result_dict.get("PACKING_SLIP", result_dict.get("packing_slip", True))
            inspection.packing_slip = bool(val)
            param_updated = "packing_slip"
            log_desc = f"Packing Slip Inspection: {'PASSED (Valid Slip Present)' if inspection.packing_slip else 'FAILED (Missing/Illegible Slip)'}"

        elif sequence_number == 9:
            # Cotton Sheet Cushioning
            val = result_dict.get("COTTON_SHEET", result_dict.get("cotton_sheet", True))
            inspection.cotton_sheet = bool(val)
            param_updated = "cotton_sheet"
            log_desc = f"Cotton Cushioning Sheet Check: {'PASSED (Present & Dry)' if inspection.cotton_sheet else 'FAILED (Missing/Wet Sheet)'}"

        elif sequence_number == 10:
            # Primer Quantity Count in 6x6 Grid (36/36 Primers)
            val = result_dict.get("PRIMER_QUANTITY_COUNT", result_dict.get("primer_quantity_count", True))
            count = result_dict.get("COUNT", result_dict.get("count", 36))
            inspection.primer_quantity_count = bool(val) if count == 36 else False
            param_updated = "primer_quantity_count"
            log_desc = f"Primer Grid Counting (Param 11): Counted {count}/36 Primers -> {'PASSED' if inspection.primer_quantity_count else 'FAILED (Count Discrepancy)'}"

        elif sequence_number == 11:
            # 2x 18-Hole Wooden Separator Trays
            val = result_dict.get("WOODEN_SHEET_18_HOLES", result_dict.get("wooden_sheet_18_holes", True))
            inspection.wooden_sheet_18_holes = bool(val)
            param_updated = "wooden_sheet_18_holes"
            log_desc = f"18-Hole Wooden Separator Trays Check: {'PASSED (2 Trays Verified)' if inspection.wooden_sheet_18_holes else 'FAILED (Damaged/Missing Trays)'}"

        elif sequence_number == 12:
            # Interior Rust & Peeling Paint (False = Clean/Pass, True = Defect/Fail)
            val = result_dict.get("INTERIOR_RUST_PEELING_PAINT", result_dict.get("interior_rust_peeling_paint", False))
            inspection.interior_rust_peeling_paint = bool(val)
            param_updated = "interior_rust_peeling_paint"
            log_desc = f"Interior Box Cavity Check: {'PASSED (Clean & Rust Free)' if not inspection.interior_rust_peeling_paint else 'FAILED (Interior Rust / Paint Peeling Detected)'}"

        # Evaluate acceptance status:
        # Criteria: 7 params True, and interior_rust_peeling_paint False
        params_evaluated = [
            inspection.stenciling_5_sides,
            inspection.explosive_label,
            inspection.wooden_sheet,
            inspection.packing_slip,
            inspection.cotton_sheet,
            inspection.primer_quantity_count,
            inspection.wooden_sheet_18_holes,
            (not inspection.interior_rust_peeling_paint) if inspection.interior_rust_peeling_paint is not None else None
        ]

        if False in params_evaluated:
            box.acceptance_status = False
        elif all(p is True for p in params_evaluated):
            box.acceptance_status = True
        else:
            box.acceptance_status = None

        if sequence_number == 12:
            box.box_inspection_status = "Completed"

        db.add(inspection)
        db.add(box)
        db.commit()
        db.refresh(inspection)
        db.refresh(box)

        # Store in Inspection State Repository
        BoxH2AInspectionRepository.inspection_results = {
            "stenciling_5_sides": inspection.stenciling_5_sides,
            "explosive_label": inspection.explosive_label,
            "wooden_sheet": inspection.wooden_sheet,
            "packing_slip": inspection.packing_slip,
            "cotton_sheet": inspection.cotton_sheet,
            "primer_quantity_count": inspection.primer_quantity_count,
            "wooden_sheet_18_holes": inspection.wooden_sheet_18_holes,
            "interior_rust_peeling_paint": inspection.interior_rust_peeling_paint,
            "acceptance_status": box.acceptance_status
        }

        # Add log
        if log_desc:
            await log_service.add_box_log(description=log_desc, box_id=box_id)

        # Broadcast live parameter update to WebSocket clients
        if param_updated:
            await inspection_box_manager.send_json({
                "type": "parameter_update",
                "object": {
                    "parameter_key": param_updated,
                    "value": getattr(inspection, param_updated),
                    "acceptance_status": box.acceptance_status
                }
            })
