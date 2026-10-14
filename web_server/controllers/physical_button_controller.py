from services.physical_button_service import PhysicalButtonService
from schemas.response_dto import ResponseDTO
from sqlmodel import Session
from core.database import get_db
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Depends, Request, Form, Response, status


router = APIRouter(prefix="/physical_button", tags=["Physical Button"])


@router.get("/box_button_pressed" )
def box_button_pressed(db: Session = Depends(get_db)):
    PhysicalButtonService().box_button_pressed()
    return ResponseDTO(
        status=True,
        message="Button Pressed successfully",
    )