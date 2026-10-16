from typing import Optional, List, Dict, Any
import asyncio
import os
import datetime
from fastapi import HTTPException
from sqlmodel import Session, select
from models.primer_1al_inspection_model import Primer1ALInspection
from services.primer_1al_inspection_service import Primer1ALInspectionService
from models.user_model import User
from models.primer_model import Primer, Fuze
from models.box_model import Box
from models.carrier_model import Carrier
from models.lot_model import Lot
from schemas.primer_dto import (
    PrimerStatusUpdateRequest, PrimerParameterUpdateRequest,
    PrimerAcceptanceStatusRequest, PrimerUpdateBoxRequest,
    FuzeStatusUpdateRequest, FuzeParameterUpdateRequest,
    FuzeAcceptanceStatusRequest
)
from services.log_service import FuzeLogService


class PrimerService:

    @staticmethod
    async def register_primers(db: Session, lot_id: int, primer_files_path: str, sequence_number: int, primer_type: str = "Primer Electric 1A/L", box_id: Optional[int] = None):
        os.makedirs(primer_files_path, exist_ok=True)
        new_primer = Primer(
            sequence_number=sequence_number,
            lot_id=lot_id,
            box_id=box_id,
            files_path=primer_files_path,
            primer_type=primer_type,
            primer_inspection_status="Pending"
        )

        inspection = Primer1ALInspection()
        db.add(inspection)
        db.commit()
        db.refresh(inspection)
        new_primer.primer_1al_inspection_id = inspection.id

        db.add(new_primer)
        db.commit()
        db.refresh(new_primer)
        return new_primer

    # Legacy alias
    register_fuzes = register_primers

    @staticmethod
    async def register_no_primer(db: Session, lot_id: int, primer_type: str = "Primer Electric 1A/L"):
        primer = Primer(
            lot_id=lot_id,
            primer_type=primer_type
        )
        primer.primer_inspection_status = "Completed"
        db.add(primer)
        db.commit()
        db.refresh(primer)

    register_no_fuze = register_no_primer

    @staticmethod
    def get_primer_current_details(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return None

        current_primer_seq = lot.primer_current_sequence or 1

        primer = db.exec(select(Primer).where(Primer.lot_id == lot.id, Primer.sequence_number == current_primer_seq)).first()
        if not primer:
            primer = db.exec(select(Primer).where(Primer.lot_id == lot.id)).first()
        if not primer:
            inspection = Primer1ALInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            primer_files_path = os.path.join(lot.files_path or f"lots/lot_{lot.id}", f"primer_sequence_number_{current_primer_seq}")
            primer = Primer(
                lot_id=lot.id,
                sequence_number=current_primer_seq,
                files_path=primer_files_path,
                primer_type=lot.primer_type or "Primer Electric 1A/L",
                primer_inspection_status="Pending",
                primer_1al_inspection_id=inspection.id
            )
            db.add(primer)
            db.commit()
            db.refresh(primer)

        inspection_dict = {}
        if not primer.primer_1al_inspection_id:
            inspection = Primer1ALInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            primer.primer_1al_inspection_id = inspection.id
            db.add(primer)
            db.commit()
        else:
            inspection = db.exec(
                select(Primer1ALInspection).where(Primer1ALInspection.id == primer.primer_1al_inspection_id)).first()
        if inspection:
            inspection_dict = {
                column.name: getattr(inspection, column.name)
                for column in Primer1ALInspection.__table__.columns
            }

        # Determine parent box and carrier sequences (1 carrier -> 4 boxes -> 18 primers)
        box_seq = None
        carrier_seq = None
        if primer.box_id:
            parent_box = db.exec(select(Box).where(Box.id == primer.box_id)).first()
            if parent_box:
                box_seq = parent_box.sequence_number
                if parent_box.carrier_id:
                    parent_carrier = db.exec(select(Carrier).where(Carrier.id == parent_box.carrier_id)).first()
                    if parent_carrier:
                        carrier_seq = parent_carrier.sequence_number
                if carrier_seq is None and box_seq:
                    carrier_seq = (box_seq - 1) // 4 + 1

        if box_seq is None and primer.sequence_number:
            box_seq = (primer.sequence_number - 1) // 18 + 1
            carrier_seq = (box_seq - 1) // 4 + 1

        return {
            "primer_id": primer.id,
            "fuze_id": primer.id,
            "box_id": primer.box_id,
            "box_sequence": box_seq,
            "carrier_sequence": carrier_seq,
            "primer_sequence": primer.sequence_number,
            "fuze_sequence": primer.sequence_number,
            "primer_type": primer.primer_type or "Primer Electric 1A/L",
            "fuze_type": primer.primer_type or "Primer Electric 1A/L",
            "primer_inspection_status": primer.primer_inspection_status,
            "fuze_inspection_status": primer.primer_inspection_status,
            "acceptance_status": primer.acceptance_status,
            "inspection": inspection_dict
        }

    get_fuze_current_details = get_primer_current_details

    @staticmethod
    async def start_primer_inspection(db: Session, primer_id: int, user_id: int, primer_type: str = None, lot_id: int = None):
        primer = db.exec(select(Primer).where(Primer.id == primer_id)).first()
        if not primer:
            return {"status": False, "message": "Primer unit not found", "object": None}

        if lot_id is None:
            lot_id = primer.lot_id
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return {"status": False, "message": "Associated lot not found", "object": None}

        if primer_type is None:
            primer_type = primer.primer_type or lot.primer_type or "Primer Electric 1A/L"

        primer.primer_inspection_status = "Inspecting"
        primer.start_time = datetime.datetime.now()
        primer.user_id = user_id
        db.add(primer)
        db.commit()
        db.refresh(primer)
        fuze_log_service = FuzeLogService(db)
        await fuze_log_service.add_fuze_log(
            description=f"Starting Inspection For Primer 1A/L : {primer_type} Of Lot : {lot.lot_number}",
            fuze_id=primer_id)

        from repositories.current_inspection_repositories import FuzeInspectionRepository
        FuzeInspectionRepository.inspection_command = "Continue"
        
        asyncio.create_task(Primer1ALInspectionService.start_inspection(
            fuze_id=primer_id,
            lot_id=lot.id,
        ))
           
        return {"status": True, "message": "Inspection started", "object": primer}

    start_fuze_inspection = start_primer_inspection

    @staticmethod
    async def update_primer_status(db: Session, request: PrimerStatusUpdateRequest):
        primer_id = getattr(request, 'primer_id', None) or getattr(request, 'fuze_id', None)
        primer = db.exec(select(Primer).where(Primer.id == primer_id)).first()
        if not primer:
            return "Primer not found", False

        primer.primer_inspection_status = request.status
        if request.status in ["Completed", "Stopped"]:
            primer.end_time = datetime.datetime.now()

        db.add(primer)
        db.commit()
        db.refresh(primer)

        # Update Repository Command
        from repositories.current_inspection_repositories import FuzeInspectionRepository
        FuzeInspectionRepository.inspection_command = request.status

        # Broadcast update
        from socket_controller.primer_inspection_socket_controller import inspection_primer_manager
        await inspection_primer_manager.send_json({
            "type": "primer_update",
            "object": {
                "primer_id": primer.id,
                "inspection_status": request.status
            }
        })

        return f"Status updated to {request.status}", True

    update_fuze_status = update_primer_status

    @staticmethod
    async def update_primer_parameter(db: Session, request: PrimerParameterUpdateRequest, current_user: User):
        primer_id = getattr(request, 'primer_id', None) or getattr(request, 'fuze_id', None)
        primer = db.exec(select(Primer).where(Primer.id == primer_id)).first()
        if not primer:
            return "Primer not found", False

        if not primer.primer_1al_inspection_id:
            inspection = Primer1ALInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            primer.primer_1al_inspection_id = inspection.id
            primer.primer_type = "Primer Electric 1A/L"
            db.add(primer)
            db.commit()
        else:
            inspection = db.exec(select(Primer1ALInspection).where(Primer1ALInspection.id == primer.primer_1al_inspection_id)).first()
            if not inspection:
                inspection = Primer1ALInspection()
                db.add(inspection)
                db.commit()
                db.refresh(inspection)
                primer.primer_1al_inspection_id = inspection.id
                db.add(primer)
                db.commit()

        if hasattr(inspection, request.parameter_key):
            setattr(inspection, request.parameter_key, request.value)
            
            # Check acceptance status across 6 parameters
            params_evaluated = [
                inspection.cleanliness_appearance,
                inspection.lot_number_match,
                (not inspection.magazine_crack_damage) if inspection.magazine_crack_damage is not None else None,
                (not inspection.paper_liner_damage_spillage) if inspection.paper_liner_damage_spillage is not None else None,
                inspection.rubber_ring_assembly,
                inspection.magazine_assembly
            ]
            if False in params_evaluated:
                primer.acceptance_status = False
            elif all(p is True for p in params_evaluated):
                primer.acceptance_status = True
            else:
                primer.acceptance_status = None
            
            action = "Passed" if request.value else "Rejected"
            fuze_log_service = FuzeLogService(db)
            await fuze_log_service.add_fuze_log(
                description=f"Update Parameter {request.parameter_key} Has Been {action} By {current_user.email}",
                fuze_id=primer_id
            )
            db.add(inspection)
            db.add(primer)
            db.commit()
            return f"Parameter {request.parameter_key} updated", True
        else:
            return f"Parameter {request.parameter_key} not found", False

    update_fuze_parameter = update_primer_parameter

    @staticmethod
    async def update_primer_acceptance_status(db: Session, request: PrimerAcceptanceStatusRequest):
        primer_id = getattr(request, 'primer_id', None) or getattr(request, 'fuze_id', None)
        primer = db.exec(select(Primer).where(Primer.id == primer_id)).first()
        if not primer:
            return "Primer not found", False

        primer.acceptance_status = request.acceptance_status
        db.add(primer)
        db.commit()
        db.refresh(primer)
        return "Acceptance Status Updated Successfully", True

    update_fuze_acceptance_status = update_primer_acceptance_status

    @staticmethod
    async def increment_primer_sequence(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return {"status": False, "message": "Lot not found"}

        current_seq = lot.primer_current_sequence if lot.primer_current_sequence else 1

        if current_seq < (lot.number_of_primer_to_inspect or 18):
            lot.primer_current_sequence = current_seq + 1
            db.add(lot)
            db.commit()
            return {"status": True, "message": "Moved to next primer"}
        else:
            lot.primer_inspection_status = "Completed"
            db.add(lot)
            db.commit()
            return {"status": False, "message": "All primers in this box completed. Please move to next box."}

    increment_fuze_sequence = increment_primer_sequence


# Backward compatibility
FuzeService = PrimerService
