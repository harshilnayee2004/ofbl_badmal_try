import os
import time
from datetime import datetime
from core.config import settings
from models.box_model import Box
from models.lot_model import Lot
from fastapi import HTTPException
from models.fuze_model import Fuze
from typing import List, Dict, Any
from models.user_model import User
from sqlmodel import Session, select
from schemas.lot_dto import LotCreate
from services.box_service import BoxService
from services.fuze_service import FuzeService
from services.carrier_service import CarrierService
from models.carrier_model import Carrier
from models.box_h2a_inspection_model import BoxH2AInspection
from models.carrier_6al_inspection_model import Carrier6ALInspection
from models.primer_1al_inspection_model import Primer1ALInspection


class LotService:

    @staticmethod
    async def create_lot(db: Session, lot_data: LotCreate, user_id: int, user_email: str):
        import math
        current_time = datetime.now()
        safe_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        lot_data.lot_number = lot_data.lot_number.strip()
        existing_lot = db.exec(select(Lot).where(Lot.lot_number == lot_data.lot_number)).first()
        if existing_lot:
            raise HTTPException(status_code=400, detail="Lot number already exists")

        new_lot = Lot(
            lot_number=lot_data.lot_number,
            created_at=current_time,
            user_id=user_id,
            inspection_status="Pending",
            files_path=settings.LOT_DETAILS_PATH + "/" + safe_time,
            carrier_current_sequence=1,
            box_current_sequence=1,
            fuze_current_sequence=1,
        )

        if lot_data.fuze_type == "Primer Electric 1A/L" or lot_data.fuze_type == "Primer 1A/L" or not lot_data.fuze_type:
            new_lot.fuze_type = "Primer Electric 1A/L"
            new_lot.carrier_type = "Carrier 6A/L"
            new_lot.box_type = "H2A"
            new_lot.container_type = "H2A"

            # Set quotas to inspect directly
            new_lot.number_of_carrier_to_inspect = lot_data.number_of_carrier_to_inspect if lot_data.number_of_carrier_to_inspect is not None else 20
            new_lot.number_of_box_to_inspect = lot_data.number_of_box_to_inspect if lot_data.number_of_box_to_inspect is not None else 60
            new_lot.number_of_fuze_to_inspect = lot_data.number_of_fuze_to_inspect if lot_data.number_of_fuze_to_inspect is not None else 315

            new_lot.number_of_carrier = lot_data.number_of_carrier or new_lot.number_of_carrier_to_inspect
            new_lot.number_of_box = lot_data.number_of_box or new_lot.number_of_box_to_inspect
            new_lot.number_of_fuze = lot_data.number_of_fuze or (lot_data.total_quantity or new_lot.number_of_fuze_to_inspect)
            new_lot.total_quantity = lot_data.total_quantity or new_lot.number_of_fuze

            new_lot.carrier_inspection_status = "Pending"
            new_lot.carrier_acceptance_status = "Pending"

        os.makedirs(new_lot.files_path, exist_ok=True)
        db.add(new_lot)
        db.commit()
        db.refresh(new_lot)

        # 1. Register carrier samples
        created_carriers = []
        if new_lot.number_of_carrier_to_inspect and new_lot.number_of_carrier_to_inspect > 0:
            for c_idx in range(new_lot.number_of_carrier_to_inspect):
                carrier_files_path = new_lot.files_path + f"/carrier_sequence_number_{str(c_idx + 1)}"
                carrier = await CarrierService.register_carrier(
                    db=db,
                    lot_id=new_lot.id,
                    sequence_number=c_idx + 1,
                    carrier_type=new_lot.carrier_type or "Carrier 6A/L",
                    files_path=carrier_files_path
                )
                created_carriers.append(carrier)

        # 2. Register box samples (1 Carrier -> 4 Boxes)
        created_boxes = []
        for index in range(new_lot.number_of_box_to_inspect or 0):
            parent_carrier_id = created_carriers[index // 4].id if created_carriers and (index // 4) < len(created_carriers) else None
            box_files_path = new_lot.files_path + f"/box_sequence_number_{str(index + 1)}"
            box = await BoxService.register_box(
                db=db,
                sequence_number=index + 1,
                lot_id=new_lot.id,
                box_type=new_lot.box_type,
                box_files_path=box_files_path,
                carrier_id=parent_carrier_id
            )
            created_boxes.append(box)

        # 3. Register primer samples (1 Box -> 18 Primers)
        for j in range(new_lot.number_of_fuze_to_inspect or 0):
            parent_box_id = created_boxes[j // 18].id if created_boxes and (j // 18) < len(created_boxes) else None
            fuze_files_path = new_lot.files_path + f"/fuze_sequence_number_{str(j + 1)}"
            await FuzeService.register_fuzes(
                db=db,
                lot_id=new_lot.id,
                fuze_type=new_lot.fuze_type,
                sequence_number=j + 1,
                fuze_files_path=fuze_files_path,
                box_id=parent_box_id
            )

        if new_lot.number_of_box_to_inspect == 0:
            await BoxService.register_no_box(db, new_lot.id, box_type=new_lot.box_type)

        return {
            "id": new_lot.id,
            "lot_number": new_lot.lot_number,
            "fuze_type": new_lot.fuze_type,
            "total_quantity": new_lot.total_quantity or new_lot.number_of_fuze,
            "carrier_type": new_lot.carrier_type,
            "number_of_carrier": new_lot.number_of_carrier,
            "number_of_carrier_to_inspect": new_lot.number_of_carrier_to_inspect,
            "carrier_acceptance_status": new_lot.carrier_acceptance_status,
            "carrier_inspection_status": new_lot.carrier_inspection_status,
            "box_type": new_lot.box_type,
            "number_box": new_lot.number_of_box,
            "number_of_box": new_lot.number_of_box,
            "number_of_box_to_inspect": new_lot.number_of_box_to_inspect,
            "box_acceptance_status": new_lot.box_acceptance_status,
            "box_inspection_status": new_lot.box_inspection_status,
            "number_of_fuze": new_lot.number_of_fuze,
            "number_of_fuze_to_inspect": new_lot.number_of_fuze_to_inspect,
            "fuze_acceptance_status": new_lot.fuze_acceptance_status,
            "fuze_inspection_status": new_lot.fuze_inspection_status,
            "inspection_status": new_lot.inspection_status,
            "created_at": new_lot.created_at,
            "created_by": user_email
        }

    @staticmethod
    def get_all_lots(db: Session) -> List[Dict[str, Any]]:
        lot_list = []
        for lot in db.exec(select(Lot)).all():
            lot_list.append(LotService.lot_db_model_to_dict(db, lot))
        return lot_list

    @staticmethod
    def get_lot_by_id(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return None
        box = db.exec(select(Box).where(Box.sequence_number == lot.box_current_sequence, Box.lot_id == lot_id)).first()
        user = db.exec(select(User).where(User.id == lot.user_id)).first() if lot.user_id else None
        if box is None:
            box = db.exec(select(Box).where(Box.lot_id == lot.id)).first()
        return {
            "lot_id": lot.id,
            "lot_number": lot.lot_number,
            "fuze_type": lot.fuze_type,
            "total_quantity": lot.total_quantity or lot.number_of_fuze,
            "carrier_type": lot.carrier_type,
            "number_of_carrier": lot.number_of_carrier,
            "number_of_carrier_to_inspect": lot.number_of_carrier_to_inspect,
            "carrier_current_sequence": lot.carrier_current_sequence,
            "carrier_count_confirmation": lot.carrier_count_confirmation,
            "carrier_acceptance_status": lot.carrier_acceptance_status,
            "carrier_inspection_status": lot.carrier_inspection_status,
            "number_of_box": lot.number_of_box,
            "number_of_fuze": lot.number_of_fuze,
            "number_of_box_to_inspect": lot.number_of_box_to_inspect,
            "number_of_fuze_to_inspect": lot.number_of_fuze_to_inspect,     
            "box_count_confirmation": lot.box_count_confirmation,
            "fuze_count_confirmation": lot.fuze_count_confirmation,
            "box_acceptance_status": lot.box_acceptance_status,
            "fuze_acceptance_status": lot.fuze_acceptance_status,
            "acceptance_status": lot.acceptance_status,
            "inspection_status": lot.inspection_status,
            "box_inspection_status": lot.box_inspection_status,
            "fuze_inspection_status": lot.fuze_inspection_status,
            "created_at": lot.created_at.strftime('%Y-%m-%d %H:%M:%S') if lot.created_at else 'N/A',
            "created_by": user.email if user else 'N/A',
            "box_type": lot.box_type,
            "box_current_sequence": lot.box_current_sequence,
            "fuze_current_sequence": lot.fuze_current_sequence
        }

    @staticmethod
    def get_lots_for_inspection(db: Session, inspection_type: str) -> List[Dict[str, Any]]:

        status_field = Lot.inspection_status

        if inspection_type == "box":
            status_field = Lot.box_inspection_status
        elif inspection_type == "fuze":
            status_field = Lot.fuze_inspection_status
        elif inspection_type == "carrier":
            status_field = Lot.carrier_inspection_status

        lots = db.exec(
            select(Lot)
            .where(status_field.in_(["Pending", "Inspecting"]))
            .order_by(Lot.id)
        ).all()

        lot_list = []
        for lot in lots:
            lot_list.append(LotService.lot_db_model_to_dict(db, lot))

        return lot_list

    @staticmethod
    def get_box_current_details(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return None
        current_seq = lot.box_current_sequence or 1

        box = db.exec(select(Box).where(Box.lot_id == lot.id, Box.sequence_number == current_seq)).first()
        if not box:
            box = db.exec(select(Box).where(Box.lot_id == lot.id)).first()
        if not box:
            # Auto-register box if missing
            parent_carrier_id = None
            if lot.number_of_carrier_to_inspect and lot.number_of_carrier_to_inspect > 0:
                c_seq = (current_seq - 1) // 4 + 1
                c_obj = db.exec(select(Carrier).where(Carrier.lot_id == lot.id, Carrier.sequence_number == c_seq)).first()
                if c_obj:
                    parent_carrier_id = c_obj.id

            inspection = BoxH2AInspection()
            db.add(inspection)
            db.commit()
            db.refresh(inspection)
            box_files_path = os.path.join(lot.files_path or f"lots/lot_{lot.id}", f"box_sequence_number_{current_seq}")
            box = Box(
                lot_id=lot.id,
                carrier_id=parent_carrier_id,
                sequence_number=current_seq,
                files_path=box_files_path,
                box_type=lot.box_type or "H2A",
                box_inspection_status="Pending",
                box_h2a_inspection_id=inspection.id
            )
            db.add(box)
            db.commit()
            db.refresh(box)

        inspection_dict = {}
        if (box.box_type in ["H2A", "Box H2A"]) or box.box_h2a_inspection_id or not box.box_type:
            if not box.box_h2a_inspection_id:
                inspection = BoxH2AInspection()
                db.add(inspection)
                db.commit()
                db.refresh(inspection)
                box.box_h2a_inspection_id = inspection.id
                db.add(box)
                db.commit()
            else:
                inspection = db.exec(
                    select(BoxH2AInspection).where(BoxH2AInspection.id == box.box_h2a_inspection_id)).first()
            if inspection:
                inspection_dict = {
                    column.name: getattr(inspection, column.name)
                    for column in BoxH2AInspection.__table__.columns
                }
        elif box.box_type == "M104":
            from models.box_M104_inspection_model import BoxM104Inspection
            inspection = db.exec(
                select(BoxM104Inspection).where(BoxM104Inspection.id == box.box_m104_inspection_id)).first()
            if inspection:
                inspection_dict = {
                    column.name: getattr(inspection, column.name)
                    for column in BoxM104Inspection.__table__.columns
                }
        elif box.box_type == "G70":
            from models.box_G70_inspection_model import BoxG70Inspection
            inspection = db.exec(
                select(BoxG70Inspection).where(BoxG70Inspection.id == box.box_g70_inspection_id)).first()
            if inspection:
                inspection_dict = {
                    column.name: getattr(inspection, column.name)
                    for column in BoxG70Inspection.__table__.columns
                }

        # Determine parent carrier sequence (1 carrier -> 4 boxes)
        carrier_seq = None
        if box.carrier_id:
            parent_carrier = db.exec(select(Carrier).where(Carrier.id == box.carrier_id)).first()
            if parent_carrier:
                carrier_seq = parent_carrier.sequence_number
        if carrier_seq is None and box.sequence_number:
            carrier_seq = (box.sequence_number - 1) // 4 + 1

        return {
            "box_id": box.id,
            "carrier_id": box.carrier_id,
            "carrier_sequence": carrier_seq,
            "box_type": box.box_type or "H2A",
            "box_sequence": box.sequence_number,
            "box_number": box.box_number,
            "inspection": inspection_dict,
            "box_inspection_status": box.box_inspection_status
        }

    @staticmethod
    def search_lots(db: Session, query: str) -> List[Dict[str, Any]]:
        lots = db.exec(select(Lot).where(Lot.lot_number.contains(query))).all()
        lot_list = []
        for lot in lots:
            lot_obj = {
                "id": lot.id,
                "lot_number": lot.lot_number,
                "fuze_type": lot.fuze_type,
                "inspection_status": lot.inspection_status
            }
            lot_list.append(lot_obj)
        return lot_list


    @staticmethod
    def increment_carrier_sequence(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return {"status": False, "message": "Lot not found"}
        curr_seq = lot.carrier_current_sequence or 1
        num_inspect = lot.number_of_carrier_to_inspect or 0

        if curr_seq < num_inspect:
            lot.carrier_current_sequence = curr_seq + 1
            db.add(lot)
            db.commit()
            db.refresh(lot)
            return {"status": True, "message": "Moved to next carrier"}
        else:
            lot.carrier_inspection_status = "Completed"
            if lot.carrier_inspection_status == "Completed" and lot.box_inspection_status == "Completed" and lot.fuze_inspection_status == "Completed":
                lot.inspection_status = "Completed"
            db.add(lot)
            db.commit()
            return {"status": False, "message": "All carriers in this lot completed. Please proceed to next level or lot."}

    @staticmethod
    def decrement_carrier_sequence(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if not lot:
            return {"status": False, "message": "Lot not found"}
        curr_seq = lot.carrier_current_sequence or 1
        if curr_seq > 1:
            lot.carrier_current_sequence = curr_seq - 1
            db.add(lot)
            db.commit()
            db.refresh(lot)
        return {"status": True, "message": "Moved to previous carrier"}

    @staticmethod
    def increment_box_sequence(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if lot.box_current_sequence <= lot.number_of_box_to_inspect:
            lot.box_current_sequence += 1
            db.add(lot)
            db.commit()
            db.refresh(lot)

        if lot.box_current_sequence <= lot.number_of_box_to_inspect:
            db.add(lot)
            db.commit()
            return {"status": True, "message": "Moved to next box"}
        else:
            lot.box_inspection_status = "Completed"
            
            boxes = db.exec(select(Box).where(Box.lot_id == lot_id)).all()
            if boxes:
                all_accepted = all(box.acceptance_status is True for box in boxes)
                lot.box_acceptance_status = "Passed" if all_accepted else "Rejected"
            
            if (lot.carrier_inspection_status in ["Completed", "Pending"] or not lot.number_of_carrier_to_inspect) and \
               lot.box_inspection_status == "Completed" and lot.fuze_inspection_status == "Completed":
                lot.inspection_status = "Completed"

            db.add(lot)
            db.commit()
            return {"status": False, "message": "All boxes in this lot completed. Please move to next lot."}

    @staticmethod
    def increment_fuze_sequence(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if lot.fuze_current_sequence <= lot.number_of_fuze_to_inspect:
            lot.fuze_current_sequence += 1
            db.add(lot)
            db.commit()
            db.refresh(lot)

        if lot.fuze_current_sequence < lot.number_of_fuze_to_inspect:
            db.add(lot)
            db.commit()
            return {"status": True, "message": "Moved to next fuze"}
        else:
            lot.fuze_inspection_status = "Completed"
            
            fuzes = db.exec(select(Fuze).where(Fuze.lot_id == lot_id)).all()
            if fuzes:
                all_accepted = all(fuze.acceptance_status is True for fuze in fuzes)
                lot.fuze_acceptance_status = "Passed" if all_accepted else "Rejected"

            if (lot.carrier_inspection_status in ["Completed", "Pending"] or not lot.number_of_carrier_to_inspect) and \
               lot.fuze_inspection_status == "Completed" and lot.box_inspection_status == "Completed":
                lot.inspection_status = "Completed"
            db.add(lot)
            db.commit()
            return {"status": False, "message": "All fuzes in this lot completed. Please move to next lot."}


    @staticmethod
    def decrement_box_sequence(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if lot.box_current_sequence > 1:
            lot.box_current_sequence -= 1
            db.add(lot)
            db.commit()
            db.refresh(lot)
        return {"status": True, "message": "Moved to previous box"}

    @staticmethod
    def decrement_fuze_sequence(db: Session, lot_id: int):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if lot.fuze_current_sequence > 1:
            lot.fuze_current_sequence -= 1
            db.add(lot)
            db.commit()
            db.refresh(lot)
        return {"status": True, "message": "Moved to previous fuze"}

    @staticmethod
    def update_lot_acceptance_status(db: Session, lot_id: int, status: str):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if lot:
            lot.acceptance_status = status
            db.add(lot)
            db.commit()
            return {"status": True, "message": "Lot acceptance status updated"}
        return {"status": False, "message": "Lot not found"}

    @staticmethod
    def lot_db_model_to_dict(db: Session, lot: Lot):
        lot_obj = {}
        lot_obj["id"] = lot.id
        lot_obj["lot_number"] = lot.lot_number
        lot_obj["fuze_type"] = lot.fuze_type
        lot_obj["total_quantity"] = lot.total_quantity or lot.number_of_fuze
        lot_obj["sampling_plan"] = lot.sampling_plan

        lot_obj["carrier_type"] = lot.carrier_type
        lot_obj["number_of_carrier"] = lot.number_of_carrier
        lot_obj["number_of_carrier_to_inspect"] = lot.number_of_carrier_to_inspect
        lot_obj["carrier_current_sequence"] = lot.carrier_current_sequence
        lot_obj["carrier_count_confirmation"] = lot.carrier_count_confirmation
        lot_obj["carrier_inspection_status"] = lot.carrier_inspection_status
        lot_obj["carrier_acceptance_status"] = lot.carrier_acceptance_status

        lot_obj["box_type"] = lot.box_type
        lot_obj["number_of_box"] = lot.number_of_box
        lot_obj["number_of_fuze"] = lot.number_of_fuze
        lot_obj["number_of_box_to_inspect"] = lot.number_of_box_to_inspect
        lot_obj["box_current_sequence"] = lot.box_current_sequence
        lot_obj["fuze_current_sequence"] = lot.fuze_current_sequence
        lot_obj["number_of_fuze_to_inspect"] = lot.number_of_fuze_to_inspect
        lot_obj["box_count_confirmation"] = lot.box_count_confirmation
        lot_obj["fuze_count_confirmation"] = lot.fuze_count_confirmation
        lot_obj["box_acceptance_status"] = lot.box_acceptance_status
        lot_obj["fuze_acceptance_status"] = lot.fuze_acceptance_status
        lot_obj["acceptance_status"] = lot.acceptance_status
        lot_obj["inspection_status"] = lot.inspection_status
        lot_obj["box_inspection_status"] = lot.box_inspection_status
        lot_obj["fuze_inspection_status"] = lot.fuze_inspection_status
        lot_obj["created_at"] = lot.created_at
        user = db.exec(select(User).where(User.id == lot.user_id)).first() if lot.user_id else None
        lot_obj["created_by"] = user.email if user else "N/A"
        return lot_obj

    @staticmethod
    def get_count_information(db: Session, lot_id: int, count_type: str):
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()

        if lot is None:
            return None

        if count_type == "carrier":
            count_val = lot.carrier_count_confirmation or 0
            type_val = lot.carrier_type or "Carrier 6A/L"
            total_val = lot.number_of_carrier
        elif count_type in ["fuze", "primer"]:
            count_val = lot.fuze_count_confirmation or 0
            type_val = lot.fuze_type
            total_val = lot.number_of_fuze
        else:
            count_val = lot.box_count_confirmation or 0
            type_val = lot.box_type
            total_val = lot.number_of_box

        return {
            "lot_id": lot_id,
            "lot_number": lot.lot_number,
            "count": count_val,
            "fuze_or_box_type": type_val,
            "number_of_boxes_or_fuzes": total_val
        }

    @staticmethod
    async def start_counting(db: Session, lot_id: int, count_type: str):
        # time.sleep(5)
        lot = db.exec(select(Lot).where(Lot.id == lot_id)).first()
        if lot is None:
            return None
        
        if count_type == "fuze":
            lot.fuze_count_confirmation = lot.fuze_count_confirmation + 1
        else:
            if M104Counting.command_counting_command == "Counting":
                return None
            count = await BoxM104InspectionService.start_counting()
            if count == -1:
                return None
            lot.box_count_confirmation = count
        db.add(lot)
        db.commit()
        db.refresh(lot)
        return {
            "lot_id": lot.id,
            "lot_number": lot.lot_number,
            "count": lot.fuze_count_confirmation if count_type == "fuze" else lot.box_count_confirmation,
            "fuze_or_box_type": lot.fuze_type if count_type == "fuze" else lot.box_type,
            "number_of_boxes_or_fuzes": lot.number_of_fuze if count_type == "fuze" else lot.number_of_box
        }

    @staticmethod
    def get_fuze_by_lot_id(db: Session, lot_id: int):
        fuzes = db.exec(select(Fuze).where(Fuze.lot_id == lot_id)).all()
        result = []
        for fuze in fuzes:
            fuze_dict = fuze.dict()
            inspection_dict = {}

            if fuze.primer_1al_inspection_id:
                inspection = db.exec(select(Primer1ALInspection).where(Primer1ALInspection.id == fuze.primer_1al_inspection_id)).first()
                if inspection:
                    for column in Primer1ALInspection.__table__.columns:
                        inspection_dict[column.name] = getattr(inspection, column.name)
            
            fuze_dict["inspection"] = inspection_dict

            media_files = []
            if getattr(fuze, "files_path", None) and os.path.exists(fuze.files_path):
                try:
                    for f in os.listdir(fuze.files_path):
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.mkv', '.webm')):
                            rel_path = os.path.relpath(os.path.join(fuze.files_path, f), settings.LOT_DETAILS_PATH)
                            media_files.append(f"/media/{rel_path}")
                except Exception:
                    pass
            fuze_dict["media_files"] = media_files
            result.append(fuze_dict)

        return result

    @staticmethod
    def get_box_by_lot_id(db: Session, lot_id: int):
        boxes = db.exec(select(Box).where(Box.lot_id == lot_id)).all()
        if len(boxes) == 1:
            return []
        
        result = []
        for box in boxes:
            box_dict = box.dict()
            
            inspection_dict = {}
            if box.box_type == "M104" and box.box_m104_inspection_id:
                inspection = db.exec(select(BoxM104Inspection).where(BoxM104Inspection.id == box.box_m104_inspection_id)).first()
                if inspection:
                    for column in BoxM104Inspection.__table__.columns:
                        inspection_dict[column.name] = getattr(inspection, column.name)
            elif box.box_type == "G70" and box.box_g70_inspection_id:
                inspection = db.exec(select(BoxG70Inspection).where(BoxG70Inspection.id == box.box_g70_inspection_id)).first()
                if inspection:
                    for column in BoxG70Inspection.__table__.columns:
                        inspection_dict[column.name] = getattr(inspection, column.name)
            box_dict["inspection"] = inspection_dict
            
            media_files = []
            if box.files_path and os.path.exists(box.files_path):
                try:
                    for f in os.listdir(box.files_path):
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov')):
                            rel_path = os.path.relpath(os.path.join(box.files_path, f), settings.LOT_DETAILS_PATH)
                            media_files.append(f"/media/{rel_path}")
                except Exception:
                    pass
            box_dict["media_files"] = media_files
            result.append(box_dict)
            
        return result


    @staticmethod
    def get_box_for_fuze_reference(db: Session, lot_id: int):
        boxes = db.exec(select(Box).where(Box.lot_id == lot_id)).all()
        if len(boxes) == 1:
            return []
        
        result = []
        for box in boxes:
            if box.box_number is None:
                continue
            box_dict={
                "box_number": box.box_number,
                "id": box.id,
                "box_type": box.box_type
            }
            result.append(box_dict)
            
        return result