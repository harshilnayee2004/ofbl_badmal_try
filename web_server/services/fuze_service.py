from typing import Optional, List, Dict, Any
import asyncio
import os
import datetime
from fastapi import HTTPException
from sqlmodel import Session, select
from models.primer_1al_inspection_model import Primer1ALInspection
from services.primer_1al_inspection_service import Primer1ALInspectionService
from models.user_model import User
from models.fuze_model import Fuze
from models.box_model import Box
from models.carrier_model import Carrier
from models.lot_model import Lot
from schemas.fuze_dto import FuzeStatusUpdateRequest, FuzeParameterUpdateRequest, \
    FuzeAcceptanceStatusRequest, FuzeUpdateBoxRequest
from services.log_service import FuzeLogService


class FuzeService:

    @staticmethod
    async def register_fuzes(db: Session, lot_id: int, fuze_files_path: str, sequence_number: int, fuze_type: str, box_id: Optional[int] = None):

        os.makedirs(fuze_files_path, exist_ok=True)
        new_fuze = Fuze(
            sequence_number=sequence_number,
            lot_id=lot_id,
            box_id=box_id,
            files_path=fuze_files_path,
            fuze_type=fuze_type,
            fuze_inspection_status="Pending"
        )

        inspection = Primer1ALInspection()
        db.add(inspection)
        db.commit()
        db.refresh(inspection)
        new_fuze.primer_1al_inspection_id = inspection.id

        db.add(new_fuze)
        db.commit()
        db.refresh(new_fuze)
        return new_fuze

    @staticmethod
    async def register_no_fuze(db: Session, lot_id: int, fuze_type: str):
        fuze = Fuze(
            lot_id=lot_id,
            fuze_type=fuze_type
        )
        fuze.fuze_inspection_status = "Completed"
        db.add(fuze)
        db.commit()
        db.refresh(fuze)

    @staticmethod
    def get_fuze_current_details(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return None

        current_fuze_seq = lot.fuze_current_sequence or 1

        fuze = db.exec(select(Fuze).where(Fuze.lot_id == lot.id, Fuze.sequence_number == current_fuze_seq)).first()
        if not fuze:
            fuze = db.exec(select(Fuze).where(Fuze.lot_id == lot.id)).first()
        if not fuze:
            # Auto-register fuze if missing
            inspection = Primer1ALInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            fuze_files_path = os.path.join(lot.files_path or f"lots/lot_{lot.id}", f"fuze_sequence_number_{current_fuze_seq}")
            fuze = Fuze(
                lot_id=lot.id,
                sequence_number=current_fuze_seq,
                files_path=fuze_files_path,
                fuze_type=lot.fuze_type or "Primer Electric 1A/L",
                fuze_inspection_status="Pending",
                primer_1al_inspection_id=inspection.id
            )
            db.add(fuze)
            db.commit()
            db.refresh(fuze)

        inspection_dict = {}
        if not fuze.primer_1al_inspection_id:
            inspection = Primer1ALInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            fuze.primer_1al_inspection_id = inspection.id
            db.add(fuze)
            db.commit()
        else:
            inspection = db.exec(
                select(Primer1ALInspection).where(Primer1ALInspection.id == fuze.primer_1al_inspection_id)).first()
        if inspection:
            inspection_dict = {
                column.name: getattr(inspection, column.name)
                for column in Primer1ALInspection.__table__.columns
            }

        # Determine parent box and carrier sequences (1 carrier -> 4 boxes -> 18 primers)
        box_seq = None
        carrier_seq = None
        if fuze.box_id:
            parent_box = db.exec(select(Box).where(Box.id == fuze.box_id)).first()
            if parent_box:
                box_seq = parent_box.sequence_number
                if parent_box.carrier_id:
                    parent_carrier = db.exec(select(Carrier).where(Carrier.id == parent_box.carrier_id)).first()
                    if parent_carrier:
                        carrier_seq = parent_carrier.sequence_number
                if carrier_seq is None and box_seq:
                    carrier_seq = (box_seq - 1) // 4 + 1

        if box_seq is None and fuze.sequence_number:
            box_seq = (fuze.sequence_number - 1) // 18 + 1
            carrier_seq = (box_seq - 1) // 4 + 1

        return {
            "fuze_id": fuze.id,
            "box_id": fuze.box_id,
            "box_sequence": box_seq,
            "carrier_sequence": carrier_seq,
            "fuze_sequence": fuze.sequence_number,
            "fuze_type": fuze.fuze_type or "Primer Electric 1A/L",
            "fuze_inspection_status": fuze.fuze_inspection_status,
            "acceptance_status": fuze.acceptance_status,
            "inspection": inspection_dict
        }

    @staticmethod
    async def start_fuze_inspection(db: Session, fuze_id: int, user_id: int, fuze_type: str = None, lot_id: int = None):
        fuze = db.exec(select(Fuze).where(Fuze.id == fuze_id)).first()
        if not fuze:
            return {"status": False, "message": "Fuze unit not found", "object": None}

        if lot_id is None:
            lot_id = fuze.lot_id
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return {"status": False, "message": "Associated lot not found", "object": None}

        if fuze_type is None:
            fuze_type = fuze.fuze_type or lot.fuze_type or "Primer Electric 1A/L"

        fuze.fuze_inspection_status = "Inspecting"
        fuze.start_time = datetime.datetime.now()
        fuze.user_id = user_id
        db.add(fuze)
        db.commit()
        db.refresh(fuze)
        fuze_log_service = FuzeLogService(db)
        await fuze_log_service.add_fuze_log(
            description=f"Starting Inspection For Unit Type : {fuze_type} Of Lot : {lot.lot_number}",
            fuze_id=fuze_id)

        from repositories.current_inspection_repositories import FuzeInspectionRepository
        FuzeInspectionRepository.inspection_command = "Continue"
        
        asyncio.create_task(Primer1ALInspectionService.start_inspection(
            fuze_id=fuze_id,
            lot_id=lot.id,
        ))
           
        return {"status": True, "message": "Inspection started", "object": fuze}

    @staticmethod
    async def update_fuze_status(db: Session, request: FuzeStatusUpdateRequest):
        fuze = db.exec(select(Fuze).where(Fuze.id == request.fuze_id)).first()
        if not fuze:
            return "Fuze not found", False

        fuze.fuze_inspection_status = request.status
        if request.status in ["Completed", "Stopped"]:
            fuze.end_time = datetime.datetime.now()

        db.add(fuze)
        db.commit()
        db.refresh(fuze)

        # Update Repository Command
        from repositories.current_inspection_repositories import FuzeInspectionRepository
        FuzeInspectionRepository.inspection_command = request.status

        # Broadcast update
        from socket_controller.fuze_inspection_socket_controller import inspection_fuze_manager
        await inspection_fuze_manager.send_json({
            "type": "fuze_update",
            "object": {
                "fuze_id": fuze.id,
                "inspection_status": request.status
            }
        })

        return f"Status updated to {request.status}", True

    @staticmethod
    async def update_fuze_parameter(db: Session, request: FuzeParameterUpdateRequest, current_user: User):
        fuze = db.exec(select(Fuze).where(Fuze.id == request.fuze_id)).first()
        if not fuze:
            return "Fuze not found", False

        if not fuze.primer_1al_inspection_id:
            inspection = Primer1ALInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            fuze.primer_1al_inspection_id = inspection.id
            fuze.fuze_type = "Primer Electric 1A/L"
            db.add(fuze)
            db.commit()
        else:
            inspection = db.exec(select(Primer1ALInspection).where(Primer1ALInspection.id == fuze.primer_1al_inspection_id)).first()
            if not inspection:
                inspection = Primer1ALInspection()
                db.add(inspection)
                db.commit()
                db.refresh(inspection)
                fuze.primer_1al_inspection_id = inspection.id
                db.add(fuze)
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
                fuze.acceptance_status = False
            elif all(p is True for p in params_evaluated):
                fuze.acceptance_status = True
            else:
                fuze.acceptance_status = None
            
            action = "Passed" if request.value else "Rejected"
            fuze_log_service = FuzeLogService(db)
            await fuze_log_service.add_fuze_log(
                description=f"Update Parameter {request.parameter_key} Has Been {action} By {current_user.email}",
                fuze_id=request.fuze_id
            )
            db.add(inspection)
            db.add(fuze)
            db.commit()
            return f"Parameter {request.parameter_key} updated", True
        else:
            return f"Parameter {request.parameter_key} not found", False

    @staticmethod
    async def update_fuze_acceptance_status(db: Session, request: FuzeAcceptanceStatusRequest):
        fuze = db.exec(select(Fuze).where(Fuze.id == request.fuze_id)).first()
        if not fuze:
            return "Fuze not found", False

        fuze.acceptance_status = request.acceptance_status
        db.add(fuze)
        db.commit()
        db.refresh(fuze)
        return "Acceptance Status Updated Successfully", True

    @staticmethod
    async def increment_fuze_sequence(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return {"status": False, "message": "Lot not found"}

        current_seq = lot.fuze_current_sequence if lot.fuze_current_sequence else 1

        if current_seq < lot.number_of_fuze_to_inspect:
            lot.fuze_current_sequence = current_seq + 1
            db.add(lot)
            db.commit()
            return {"status": True, "message": "Moved to next fuze"}
        else:
            lot.fuze_inspection_status = "Completed"
            db.add(lot)
            db.commit()
            return {"status": False, "message": "All fuzes in this box completed. Please move to next box."}