from sqlmodel import Session
from core.database import get_db
from models.user_model import User
from fastapi import APIRouter, Depends
from core.deps import get_current_user
from schemas.response_dto import ResponseDTO
from services.carrier_service import CarrierService
import datetime
from schemas.carrier_dto import (
    CarrierStartInspectionRequest,
    CarrierStatusUpdateRequest,
    CarrierParameterUpdateRequest,
    CarrierNumberUpdateRequest,
    CarrierAcceptanceStatusRequest
)

router = APIRouter(
    prefix="/carrier",
    tags=["Carriers"]
)

@router.get("/get_carrier_logs/{carrier_id}")
async def get_carrier_logs(carrier_id: int, db: Session = Depends(get_db)):
    from services.log_service import CarrierLogService
    log_service = CarrierLogService(db)
    logs = log_service.get_carrier_logs(carrier_id)
    return ResponseDTO(message="Carrier Logs Fetched Successfully", status=True, object=logs)

@router.post("/start_inspection")
async def start_inspection(
    request: CarrierStartInspectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await CarrierService.start_carrier_inspection(
        db=db,
        carrier_id=request.carrier_id,
        user_id=current_user.id,
        carrier_type=request.carrier_type or "Carrier 6A/L",
        lot_id=request.lot_id
    )
    return ResponseDTO(message=result.get("message"), status=result.get("status"), object=result.get("object"))

@router.get("/get_carrier_current_details/{lot_id}")
def get_carrier_current_details(lot_id: int, db: Session = Depends(get_db)):
    result = CarrierService.get_carrier_current_details(db, lot_id)
    if result:
        from repositories.current_inspection_repositories import CarrierInspectionRepository
        result["recording_status"] = CarrierInspectionRepository.recording_status
    return ResponseDTO(message="Carrier Details Fetched Successfully", status=True, object=result)

@router.post("/update_status")
async def update_carrier_status(
    request: CarrierStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message, success = await CarrierService.update_carrier_status(db=db, request=request)
    return ResponseDTO(message=message, status=success, object={"status": request.status})

@router.post("/update_parameter")
async def update_carrier_parameter(
    request: CarrierParameterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message, status = await CarrierService.update_carrier_parameter(db=db, request=request, current_user=current_user)
    return ResponseDTO(message=message, status=status, object=None)

@router.get("/get_current_inspection_state")
async def get_current_inspection_state(current_user: User = Depends(get_current_user)):
    from repositories.current_inspection_repositories import CarrierInspectionRepository
    
    wait_time = CarrierInspectionRepository.current_wait_time
    if CarrierInspectionRepository.timer_start_time and wait_time > 0:
        elapsed = (datetime.datetime.now() - CarrierInspectionRepository.timer_start_time).total_seconds()
        wait_time = max(0, int(wait_time - elapsed))

    return ResponseDTO(
        message="Current state fetched",
        status=True,
        object={
            "instruction": CarrierInspectionRepository.current_inspection_instruction,
            "wait_time": wait_time,
            "recording_status": CarrierInspectionRepository.recording_status
        }
    )

@router.post("/update_carrier_number")
async def update_carrier_number(
    request: CarrierNumberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message, status = await CarrierService.update_carrier_number(db=db, request=request, current_user=current_user)
    return ResponseDTO(message=message, status=status, object=None)
