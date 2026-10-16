from sqlmodel import Session
from core.database import get_db
from models.user_model import User
from fastapi import APIRouter, Depends
from core.deps import get_current_user
from schemas.response_dto import ResponseDTO
from services.primer_service import PrimerService
from schemas.primer_dto import (
    PrimerStartInspectionRequest, PrimerStatusUpdateRequest, PrimerParameterUpdateRequest,
    PrimerAcceptanceStatusRequest, PrimerUpdateBoxRequest,
    FuzeStartInspectionRequest, FuzeStatusUpdateRequest, FuzeParameterUpdateRequest,
    FuzeAcceptanceStatusRequest, FuzeUpdateBoxRequest
)

router = APIRouter(
    prefix="/primer",
    tags=["Primers"]
)

# Also expose /fuze router for backward compatibility
legacy_fuze_router = APIRouter(
    prefix="/fuze",
    tags=["Primers (Legacy)"]
)


@router.get("/get_primer_logs/{primer_id}")
@legacy_fuze_router.get("/get_fuze_logs/{primer_id}")
async def get_primer_logs(primer_id: int, db: Session = Depends(get_db)):
    from services.log_service import FuzeLogService
    log_service = FuzeLogService(db)
    logs = log_service.get_fuze_logs(primer_id)
    return ResponseDTO(message="Logs Fetched Successfully", status=True, object=logs)


@router.post("/start_inspection")
@legacy_fuze_router.post("/start_inspection")
async def start_inspection(
        request: PrimerStartInspectionRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    primer_id = getattr(request, 'primer_id', None) or getattr(request, 'fuze_id', None)
    result = await PrimerService.start_primer_inspection(db, primer_id, current_user.id)
    return ResponseDTO(message=result.get('message'), status=result.get('status'), object=result.get("object"))


@router.get("/get_primer_current_details/{lot_id}")
@router.get("/get_fuze_current_details/{lot_id}")
@legacy_fuze_router.get("/get_fuze_current_details/{lot_id}")
def get_primer_current_details(lot_id: int, db: Session = Depends(get_db)):
    result = PrimerService.get_primer_current_details(db, lot_id)
    if result:
        from repositories.current_inspection_repositories import FuzeInspectionRepository
        result["recording_status"] = FuzeInspectionRepository.recording_status
    return ResponseDTO(message="Primer Details Fetched Successfully", status=True, object=result)


@router.get("/get_current_inspection_state")
@legacy_fuze_router.get("/get_current_inspection_state")
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
@legacy_fuze_router.post("/update_status")
async def update_primer_status(
        request: PrimerStatusUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    message, success = await PrimerService.update_primer_status(db=db, request=request)
    return ResponseDTO(message=message, status=success, object={"status": request.status})


@router.post("/update_parameter")
@legacy_fuze_router.post("/update_parameter")
async def update_primer_parameter(
        request: PrimerParameterUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    message, status = await PrimerService.update_primer_parameter(db=db, request=request, current_user=current_user)
    return ResponseDTO(message=message, status=status, object=None)


@router.post("/update_acceptance_status")
@legacy_fuze_router.post("/update_acceptance_status")
async def update_acceptance_status(
        request: PrimerAcceptanceStatusRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    message, status = await PrimerService.update_primer_acceptance_status(db=db, request=request)
    return ResponseDTO(message=message, status=status, object=None)
