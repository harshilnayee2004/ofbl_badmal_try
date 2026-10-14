from typing import Optional, List, Dict, Any
import os
import asyncio
from datetime import datetime
from sqlmodel import Session, select
from models.carrier_model import Carrier
from models.carrier_6al_inspection_model import Carrier6ALInspection
from models.box_model import Box
from models.lot_model import Lot
from models.user_model import User
from schemas.carrier_dto import (
    CarrierStartInspectionRequest,
    CarrierStatusUpdateRequest,
    CarrierParameterUpdateRequest,
    CarrierNumberUpdateRequest,
    CarrierAcceptanceStatusRequest
)
from services.carrier_6al_inspection_service import Carrier6ALInspectionService
from services.log_service import CarrierLogService
from socket_controller.carrier_inspection_socket_controller import inspection_carrier_manager
from socket_controller.lot_inspection_socket_controller import inspection_lot_manager
from repositories.current_inspection_repositories import CarrierInspectionRepository

class CarrierService:

    @staticmethod
    async def register_carrier(db: Session, lot_id: int, files_path: str, sequence_number: int, carrier_type: str = "Carrier 6A/L"):
        os.makedirs(files_path, exist_ok=True)
        carrier = Carrier(
            lot_id=lot_id,
            sequence_number=sequence_number,
            files_path=files_path,
            carrier_type=carrier_type,
            carrier_inspection_status="Pending"
        )
        inspection = Carrier6ALInspection()
        db.add(inspection)
        db.commit()
        db.refresh(inspection)

        carrier.carrier_6al_inspection_id = inspection.id
        db.add(carrier)
        db.commit()
        db.refresh(carrier)
        return carrier

    @staticmethod
    def get_carrier_current_details(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return None

        current_seq = lot.carrier_current_sequence or 1
        carrier = db.exec(select(Carrier).where(Carrier.lot_id == lot.id, Carrier.sequence_number == current_seq)).first()
        if not carrier:
            carrier = db.exec(select(Carrier).where(Carrier.lot_id == lot.id)).first()
        if not carrier:
            # Auto-register carrier if missing
            inspection = Carrier6ALInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            carrier_files_path = os.path.join(lot.files_path or f"lots/lot_{lot.id}", f"carrier_sequence_number_{current_seq}")
            carrier = Carrier(
                lot_id=lot.id,
                sequence_number=current_seq,
                files_path=carrier_files_path,
                carrier_type=lot.carrier_type or "Carrier 6A/L",
                carrier_inspection_status="Pending",
                carrier_6al_inspection_id=inspection.id
            )
            db.add(carrier)
            db.commit()
            db.refresh(carrier)

        inspection_dict = {}
        if not carrier.carrier_6al_inspection_id:
            inspection = Carrier6ALInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            carrier.carrier_6al_inspection_id = inspection.id
            db.add(carrier)
            db.commit()
        else:
            inspection = db.exec(select(Carrier6ALInspection).where(Carrier6ALInspection.id == carrier.carrier_6al_inspection_id)).first()

        if inspection:
            inspection_dict = {
                column.name: getattr(inspection, column.name)
                for column in Carrier6ALInspection.__table__.columns
            }

        child_boxes = []
        if carrier.id:
            b_records = db.exec(select(Box).where(Box.carrier_id == carrier.id)).all()
            child_boxes = [b.sequence_number for b in b_records]
        if not child_boxes and carrier.sequence_number:
            start_box = (carrier.sequence_number - 1) * 4 + 1
            child_boxes = list(range(start_box, start_box + 5))[:4]

        return {
            "carrier_id": carrier.id,
            "carrier_sequence": carrier.sequence_number,
            "carrier_number": carrier.carrier_number,
            "carrier_type": carrier.carrier_type or "Carrier 6A/L",
            "carrier_inspection_status": carrier.carrier_inspection_status,
            "acceptance_status": carrier.acceptance_status,
            "child_boxes": child_boxes,
            "inspection": inspection_dict
        }

    @staticmethod
    async def start_carrier_inspection(db: Session, carrier_id: int, user_id: int, carrier_type: str = "Carrier 6A/L", lot_id: int = None):
        carrier = db.exec(select(Carrier).where(Carrier.id == carrier_id)).first()
        if not carrier:
            return {"status": False, "message": "Carrier not found", "object": None}

        if lot_id is None:
            lot_id = carrier.lot_id
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return {"status": False, "message": "Associated lot not found", "object": None}

        carrier.carrier_inspection_status = "Inspecting"
        carrier.start_time = datetime.now()
        carrier.user_id = user_id
        db.add(carrier)
        db.commit()
        db.refresh(carrier)

        carrier_log_service = CarrierLogService(db)
        await carrier_log_service.add_carrier_log(
            description=f"Starting Inspection For Carrier Type: {carrier_type} Of Lot: {lot.lot_number}",
            carrier_id=carrier_id
        )

        CarrierInspectionRepository.inspection_command = "Continue"

        asyncio.create_task(Carrier6ALInspectionService.start_inspection(
            carrier_id=carrier_id,
            lot_number=lot.lot_number
        ))

        return {"status": True, "message": "Inspection started", "object": carrier}

    @staticmethod
    async def update_carrier_status(db: Session, request: CarrierStatusUpdateRequest):
        carrier = db.exec(select(Carrier).where(Carrier.id == request.carrier_id)).first()
        if not carrier:
            return "Carrier not found", False

        carrier.carrier_inspection_status = request.status
        if request.status in ["Completed", "Stopped"]:
            carrier.end_time = datetime.now()

        db.add(carrier)
        db.commit()
        db.refresh(carrier)

        CarrierInspectionRepository.inspection_command = request.status

        await inspection_carrier_manager.send_json({
            "type": "carrier_update",
            "object": {
                "carrier_id": carrier.id,
                "carrier_inspection_status": request.status
            }
        })

        return f"Status updated to {request.status}", True

    @staticmethod
    async def update_carrier_parameter(db: Session, request: CarrierParameterUpdateRequest, current_user: User):
        carrier = db.exec(select(Carrier).where(Carrier.id == request.carrier_id)).first()
        if not carrier or not carrier.carrier_6al_inspection_id:
            return "Carrier or inspection record not found", False

        inspection = db.exec(select(Carrier6ALInspection).where(Carrier6ALInspection.id == carrier.carrier_6al_inspection_id)).first()
        if not inspection or not hasattr(inspection, request.parameter_key):
            return f"Invalid parameter key: {request.parameter_key}", False

        setattr(inspection, request.parameter_key, request.value)

        # Check acceptance status across 5 parameters
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

        db.add(inspection)
        db.add(carrier)

        action = "Passed" if request.value else "Rejected"
        param_label = request.parameter_key.replace("_", " ").title()
        log_service = CarrierLogService(db)
        await log_service.add_carrier_log(
            description=f"Manual Override: Parameter {param_label} marked as {action} by {current_user.email}",
            carrier_id=request.carrier_id
        )

        db.commit()

        await inspection_carrier_manager.send_json({
            "type": "parameter_update",
            "object": {
                "parameter_key": request.parameter_key,
                "value": getattr(inspection, request.parameter_key),
                "acceptance_status": carrier.acceptance_status
            }
        })

        return f"Parameter {request.parameter_key} updated", True

    @staticmethod
    async def update_carrier_number(db: Session, request: CarrierNumberUpdateRequest, current_user: User):
        carrier = db.exec(select(Carrier).where(Carrier.id == request.carrier_id)).first()
        if not carrier:
            return "Carrier Not Found", False
        if carrier.carrier_number == request.new_carrier_number:
            return "Carrier Number Updated Successfully", True
        existing_carrier = db.exec(select(Carrier).where(Carrier.carrier_number == request.new_carrier_number, Carrier.lot_id == request.lot_id)).first()
        if existing_carrier:
            return "Carrier Number Already Exists", False

        old_number = carrier.carrier_number
        carrier.carrier_number = request.new_carrier_number
        db.add(carrier)

        carrier_log_service = CarrierLogService(db)
        await carrier_log_service.add_carrier_log(
            description=f"Carrier Number Changed From {old_number} To {request.new_carrier_number} By {current_user.email}",
            carrier_id=request.carrier_id
        )

        db.commit()
        return "Carrier Number Updated Successfully", True
