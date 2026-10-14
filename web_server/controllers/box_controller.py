import datetime
from sqlmodel import Session
from core.database import get_db
from models.user_model import User
from core.deps import get_current_user
from services.box_service import BoxService
from services.lot_service import LotService
from schemas.response_dto import ResponseDTO
from fastapi import APIRouter, Depends, Query
from schemas.box_dto import BoxStartInspectionRequest, BoxStatusUpdateRequest, BoxParameterUpdateRequest, BoxNumberUpdateRequest, BoxAcceptanceStatusRequest

router = APIRouter(
    prefix="/box",
    tags=["Boxes"]
)

@router.post("/start_inspection")
async def start_inspection(
    request: BoxStartInspectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await BoxService.start_box_inspection(
        db, request.box_id, request.box_type, request.lot_id, current_user.id, request.suppress_cam_error
    )
    return ResponseDTO(message="Inspection Started Successfully", status=True, object=result)

@router.get("/get_box_current_details/{lot_id}")
def get_box_current_details(lot_id:int,db: Session = Depends(get_db)):
    result=LotService.get_box_current_details(db,lot_id)
    return ResponseDTO(message="Lots Fetched Successfully",status=True,object=result)

@router.post("/update_status")
async def update_box_status(
    request: BoxStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message, success = await BoxService.update_box_status(db=db, request=request)
    return ResponseDTO(message=message, status=success, object={"status": request.status})

@router.get("/get_box_logs/{box_id}")
async def get_box_logs(box_id: int, db: Session = Depends(get_db)):
    from services.log_service import BoxLogService
    log_service = BoxLogService(db)
    logs = log_service.get_box_logs(box_id)
    return ResponseDTO(message="Logs Fetched Successfully", status=True, object=logs)

@router.post("/update_parameter")
async def update_box_parameter(
    request: BoxParameterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message, status = await BoxService.update_box_parameter(db=db, request=request, current_user=current_user)
    return ResponseDTO(message=message, status=status, object=None)

@router.get("/get_current_inspection_state")
async def get_current_inspection_state(current_user: User = Depends(get_current_user)):
    from repositories.current_inspection_repositories import BoxInspectionRepository
    
    wait_time = BoxInspectionRepository.current_wait_time
    if BoxInspectionRepository.timer_start_time and wait_time > 0:
        elapsed = (datetime.datetime.now() - BoxInspectionRepository.timer_start_time).total_seconds()
        wait_time = max(0, int(wait_time - elapsed))

    return ResponseDTO(
        message="Current state fetched",
        status=True,
        object={
            "instruction": BoxInspectionRepository.current_inspection_instruction,
            "wait_time": wait_time,
            "recording_status": BoxInspectionRepository.recording_status
        }
    )

@router.get("/get_boxes_for_fuze_inspection")
async def get_boxes_for_fuze_inspection(lot_id: int = Query(...), db: Session = Depends(get_db)):
    boxes = await BoxService.get_boxes_for_fuze_inspection(db, lot_id)
    return ResponseDTO(message="Boxes Fetched Successfully", status=True, object=boxes)

@router.post("/update_box_number")
async def update_box_number(
    request: BoxNumberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message, status = await BoxService.update_box_number(db=db, request=request, current_user=current_user)
    return ResponseDTO(message=message, status=status, object=None)

@router.post("/update_acceptance_status")
async def update_acceptance_status(
    request: BoxAcceptanceStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message, status = await BoxService.update_box_acceptance_status(db=db, request=request, current_user=current_user)
    return ResponseDTO(message=message, status=status, object=None)                 

