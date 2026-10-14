from models.user_model import User
from fastapi.responses import HTMLResponse
from core.deps import get_surveillance_user
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Depends, Request

router = APIRouter(
    prefix="/surveillance",
    tags=["Surveillance"],
    dependencies=[Depends(get_surveillance_user)] # Protect entire router with admin/surveillance check
)
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, current_user: User = Depends(get_surveillance_user)):
    return templates.TemplateResponse(
        request=request,
        name="surveillance/dashboard.html",
        context={
            "user": current_user
        }
    )

@router.get("/ptz", response_class=HTMLResponse)
def ptz_control(request: Request, current_user: User = Depends(get_surveillance_user)):
    return templates.TemplateResponse(
        request=request,
        name="surveillance/ptz_control.html",
        context={
            "user": current_user
        }
    )