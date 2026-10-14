from sqlmodel import Session
from core.database import get_db
from models.user_model import User
from fastapi import APIRouter, Depends
from core.deps import get_current_user
from schemas.response_dto import ResponseDTO
from services.fuze_service import FuzeService
from schemas.fuze_dto import FuzeStartInspectionRequest, FuzeStatusUpdateRequest, FuzeParameterUpdateRequest, \
    FuzeAcceptanceStatusRequest, FuzeUpdateBoxRequest

router = APIRouter(
    prefix="/fuze",
    tags=["Fuzes"]
)


@router.get("/get_fuze_logs/{fuze_id}")
async def get_fuze_logs(fuze_id: int, db: Session = Depends(get_db)):
    from services.log_service import FuzeLogService
    log_service = FuzeLogService(db)
    logs = log_service.get_fuze_logs(fuze_id)
    return ResponseDTO(message="Logs Fetched Successfully", status=True, object=logs)


@router.post("/start_inspection")
async def start_inspection(
        request: FuzeStartInspectionRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = await FuzeService.start_fuze_inspection(db, request.fuze_id, current_user.id)
    return ResponseDTO(message=result.get('message'), status=result.get('status'), object=result.get("object"))


@router.get("/get_fuze_current_details/{lot_id}")
def get_fuze_current_details(lot_id: int, db: Session = Depends(get_db)):
    result = FuzeService.get_fuze_current_details(db, lot_id)
    if result:
        from repositories.current_inspection_repositories import FuzeInspectionRepository
        result["recording_status"] = FuzeInspectionRepository.recording_status
    return ResponseDTO(message="Fuze Details Fetched Successfully", status=True, object=result)


@router.get("/get_current_inspection_state")
async def get_current_inspection_state(current_user: User = Depends(get_current_user)):
    import datetime
    from repositories.current_inspection_repositories import FuzeInspectionRepository

    wait_time = FuzeInspectionRepository.current_wait_time
    if FuzeInspectionRepository.timer_start_time and wait_time > 0:
        elapsed = (datetime.datetime.now() - FuzeInspectionRepository.timer_start_time).total_seconds()
        wait_time = max(0, int(wait_time - elapsed))

    return ResponseDTO(
        message="Current state fetched",
        status=True,
        object={
            "instruction": FuzeInspectionRepository.current_inspection_instruction,
            "wait_time": wait_time,
            "recording_status": FuzeInspectionRepository.recording_status
        }
    )


@router.post("/update_status")
async def update_fuze_status(
        request: FuzeStatusUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    message, success = await FuzeService.update_fuze_status(db=db, request=request)
    return ResponseDTO(message=message, status=success, object={"status": request.status})


@router.post("/update_parameter")
async def update_fuze_parameter(
        request: FuzeParameterUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    message, status = await FuzeService.update_fuze_parameter(db=db, request=request, current_user=current_user)
    return ResponseDTO(message=message, status=status, object=None)

@router.post("/update_acceptance_status")
async def update_acceptance_status(
        request: FuzeAcceptanceStatusRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    message, status = await FuzeService.update_fuze_acceptance_status(db=db, request=request)
    return ResponseDTO(message=message, status=status, object=None)

@router.post("/update_box_reference")
async def update_box_reference(
        request: FuzeUpdateBoxRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    message, status = await FuzeService.update_box_reference(db=db, request=request)
    return ResponseDTO(message=message, status=status, object=None)
