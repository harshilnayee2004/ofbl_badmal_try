from typing import Optional, List, Dict, Any
from schemas.box_dto import BoxAcceptanceStatusRequest
from schemas.box_dto import BoxParameterUpdateRequest
import os
import asyncio
from datetime import datetime
from models.box_model import Box
from models.lot_model import Lot
from models.user_model import User
from models.primer_model import Primer as Fuze
from sqlmodel import Session, select
from services.log_service import BoxLogService
from models.box_h2a_inspection_model import BoxH2AInspection
from services.box_h2a_inspection_service import BoxH2AInspectionService
from schemas.box_dto import BoxStatusUpdateRequest,BoxNumberUpdateRequest
from socket_controller.lot_inspection_socket_controller import inspection_lot_manager


class BoxService:


    @staticmethod
    async def register_box(db: Session, sequence_number: int, lot_id: int, box_type: str, box_files_path: str, carrier_id: Optional[int] = None):

        os.makedirs(box_files_path, exist_ok=True)
        box = Box(
            lot_id=lot_id,
            carrier_id=carrier_id,
            box_type=box_type or "H2A",
            sequence_number=sequence_number,
            files_path=box_files_path
        )
        inspection = BoxH2AInspection()
        db.add(inspection)
        db.commit()
        db.refresh(inspection)
        box.box_h2a_inspection_id = inspection.id
        box.box_inspection_status = "Pending"

        db.add(box)
        db.commit()
        db.refresh(box)
        return box

    @staticmethod
    async def register_no_box(db: Session, lot_id: int,box_type:str,):

        box = Box(
            lot_id=lot_id,
            box_type=box_type,
            box_number=0
        )
        box.box_inspection_status = "Completed"
        db.add(box)
        db.commit()
        db.refresh(box)
       




    @staticmethod
    async def update_box_status(db:Session,request: BoxStatusUpdateRequest):
        box_obj = db.exec(select(Box).where(Box.id == request.box_id)).first()
        if not box_obj:
            return "Box Not Found", False

        box_obj.box_inspection_status = request.status
        db.add(box_obj)
        db.commit()
        db.refresh(box_obj)

        # Also update the repository command for the background task
        from repositories.current_inspection_repositories import BoxInspectionRepository

        BoxInspectionRepository.inspection_command = request.status

        # Broadcast update to frontend
        from socket_controller.box_inspection_socket_controller import inspection_box_manager
        await inspection_box_manager.send_json({
            "type": "box_update",
            "object": {
                "box_id": box_obj.id,
                "box_inspection_status": request.status
            }
        })

        return f"Status updated to {request.status}", True

    @staticmethod
    async def start_box_inspection(db: Session, box_id: int, box_type: str, lot_id: int, user_id: int, suppress_cam_error: bool = False):
        return await BoxService.start_inspection(db=db, box_type=box_type, lot_id=lot_id, box_id=box_id, user_id=user_id, suppress_cam_error=suppress_cam_error)

    @staticmethod
    async def start_inspection(db: Session, box_type: str, lot_id: int, box_id: int, user_id: int, suppress_cam_error: bool = False):
        from repositories.camera_repositories import CameraRepository
        if suppress_cam_error is not None:
            CameraRepository.suppress_camera_error = bool(suppress_cam_error)

        box = db.exec(select(Box).where(Box.id == box_id)).first()
        if not box:
            return "Box Not Found", False

        lot_obj = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot_obj:
            return "Lot Not Found", False

        box.box_inspection_status = "Inspecting"
        box.start_time = datetime.now()
        box.user_id = user_id
        db.add(box)
        db.commit()
        db.refresh(box)

        box_log_service = BoxLogService(db)
        await box_log_service.add_box_log(
            description=f"Starting Inspection For Box Type : {box_type} Of Lot : {lot_obj.lot_number}",
            box_id=box_id)

        from repositories.current_inspection_repositories import BoxInspectionRepository
        BoxInspectionRepository.inspection_command = "Continue"

        asyncio.create_task(BoxH2AInspectionService.start_inspection(
            box_id=box_id,
            lot_number=lot_obj.lot_number,
            suppress_cam_error=suppress_cam_error
        ))

        return {"status": True, "message": "Inspection started"}

    @staticmethod
    async def update_box_parameter(db: Session, request: BoxParameterUpdateRequest, current_user: User):
        box_obj = db.exec(select(Box).where(Box.id == request.box_id)).first()
        if not box_obj:
            return "Box Not Found", False

        h2a_keys = {
            "stenciling_5_sides", "explosive_label", "wooden_sheet", "packing_slip",
            "cotton_sheet", "primer_quantity_count", "wooden_sheet_18_holes", "interior_rust_peeling_paint"
        }

        if request.parameter_key in h2a_keys or (box_obj.box_type in ["H2A", "Box H2A"]) or box_obj.box_h2a_inspection_id:
            if not box_obj.box_h2a_inspection_id:
                inspection_obj = BoxH2AInspection()
                db.add(inspection_obj)
                db.commit()
                db.refresh(inspection_obj)
                box_obj.box_h2a_inspection_id = inspection_obj.id
                box_obj.box_type = "H2A"
                db.add(box_obj)
                db.commit()
            else:
                inspection_obj = db.exec(select(BoxH2AInspection).where(BoxH2AInspection.id == box_obj.box_h2a_inspection_id)).first()
                if not inspection_obj:
                    inspection_obj = BoxH2AInspection()
                    db.add(inspection_obj)
                    db.commit()
                    db.refresh(inspection_obj)
                    box_obj.box_h2a_inspection_id = inspection_obj.id
                    db.add(box_obj)
                    db.commit()

            if hasattr(inspection_obj, request.parameter_key):
                setattr(inspection_obj, request.parameter_key, request.value)
                
                # Check acceptance status across 8 parameters
                params_evaluated = [
                    inspection_obj.stenciling_5_sides,
                    inspection_obj.explosive_label,
                    inspection_obj.wooden_sheet,
                    inspection_obj.packing_slip,
                    inspection_obj.cotton_sheet,
                    inspection_obj.primer_quantity_count,
                    inspection_obj.wooden_sheet_18_holes,
                    (not inspection_obj.interior_rust_peeling_paint) if inspection_obj.interior_rust_peeling_paint is not None else None
                ]
                if False in params_evaluated:
                    box_obj.acceptance_status = False
                elif all(p is True for p in params_evaluated):
                    box_obj.acceptance_status = True
                else:
                    box_obj.acceptance_status = None
                
                db.add(inspection_obj)
                db.add(box_obj)
                
                action = "Passed" if request.value else "Rejected"
                param_label = request.parameter_key.replace("_", " ").title()
                box_log_service = BoxLogService(db)
                await box_log_service.add_box_log(
                    description=f"Update Parameter {param_label} Has Been {action} By {current_user.email}",
                    box_id=request.box_id
                )
                db.commit()
                return f"Parameter {request.parameter_key} Updated", True
        
        return "Inspection not found or invalid box parameter", False

    @staticmethod
    async def update_box_number(db: Session, request: BoxNumberUpdateRequest, current_user: User):
        box = db.exec(select(Box).where(Box.id == request.box_id)).first()
        if not box:
            return "Box Not Found", False
        if box.box_number == request.new_box_number:
            return "Box Number Updated Successfully", True
        existing_box = db.exec(select(Box).where(Box.box_number == request.new_box_number, Box.lot_id == request.lot_id)).first()
        if existing_box:
             return "Box Number Already Exists", False

        old_number = box.box_number
        box.box_number = request.new_box_number
        db.add(box)

        # Log the change
        box_log_service = BoxLogService(db)
        await box_log_service.add_box_log(
            description=f"Box Number Changed From {old_number} To {request.new_box_number} By {current_user.email}",
            box_id=request.box_id
        )

        db.commit()
        return "Box Number Updated Successfully", True

    @staticmethod
    async def update_box_acceptance_status(db: Session, request: BoxAcceptanceStatusRequest, current_user: User):
        box_obj = db.exec(select(Box).where(Box.id == request.box_id)).first()
        if not box_obj:
            return "Box Not Found", False

        box_obj.acceptance_status = request.acceptance_status
        db.add(box_obj)

        choice = "Accepted" if request.acceptance_status else "Rejected"
        
        # Log the change
        box_log_service = BoxLogService(db)
        await box_log_service.add_box_log(
            description=f"Box Acceptance Status Set To {choice} By {current_user.email}",
            box_id=request.box_id
        )

        db.commit()
        return f"Box Marked As {choice}", True

    @staticmethod
    async def get_boxes_for_fuze_inspection(db: Session, lot_id: int):
        boxes = db.exec(select(Box).where(Box.lot_id == lot_id, Box.box_inspection_status != "Pending")).all()

        return boxes

    get_boxes_for_primer_inspection = get_boxes_for_fuze_inspection
