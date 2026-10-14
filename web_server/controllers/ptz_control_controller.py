from schemas.response_dto import ResponseDTO
from models.user_model import User
from fastapi.responses import HTMLResponse
from core.deps import get_surveillance_user
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Depends, Request
from services.ptz_control_service import PTZControlService

router = APIRouter(
    prefix="/ptz_control",
    tags=["PTZ_Control"],
)


@router.get("/1/start_action/{command}")
def start_action_1(command:int):
    PTZControlService.start_action_1(command=command)
    return ResponseDTO(
        status=True,
        message="Inspection result received successfully",
        object=None
    )

@router.get("/1/end_action/{command}")
def end_action_1(command:int):
    PTZControlService.end_action_1(command=command)
    return ResponseDTO(
        status=True,
        message="Inspection result received successfully",
        object=None
    )