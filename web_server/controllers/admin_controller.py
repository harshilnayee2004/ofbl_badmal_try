from core.database import get_db
from models.lot_model import Lot
from models.carrier_model import Carrier
from models.box_model import Box
from models.user_model import User
from models.fuze_model import Fuze
from core.deps import get_admin_user
from sqlmodel import Session, select, func
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Depends, Request

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_admin_user)] # Protect entire router with admin check
)
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, current_user: User = Depends(get_admin_user)):
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "user": current_user
        }
    )

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, current_user: User = Depends(get_admin_user)):
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "user": current_user
        }
    )

@router.get("/users", response_class=HTMLResponse)
def users_page(request: Request, current_user: User = Depends(get_admin_user)):
    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context={
            "user": current_user
        }
    )

@router.get("/cameras", response_class=HTMLResponse)
def cameras_page(request: Request, current_user: User = Depends(get_admin_user)):
    return templates.TemplateResponse(
        request=request,
        name="admin/cameras.html",
        context={
            "user": current_user
        }
    )

from typing import Optional

@router.get("/manage_lots", response_class=HTMLResponse)
def manage_lots_page(request: Request, lot_id: Optional[int] = None, current_user: User = Depends(get_admin_user)):
    if lot_id is not None:
        template_name = "admin/manage_lots/lot_details.html"
    else:
        template_name = "admin/manage_lots/view_lots.html"
        
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "user": current_user,
            "lot_id": lot_id
        }
    )

@router.get("/surveillance", response_class=HTMLResponse)
def surveillance_page(request: Request, current_user: User = Depends(get_admin_user)):
    template_name = "admin/surveillance.html"
        
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "user": current_user,
        }
    )

@router.get("/api/stats/counts")
def get_dashboard_counts(db: Session = Depends(get_db)):
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_lots = db.scalar(select(func.count(Lot.id))) or 0
    total_carriers = db.scalar(select(func.count(Carrier.id))) or 0
    total_boxes = db.scalar(select(func.count(Box.id))) or 0
    total_fuzes = db.scalar(select(func.count(Fuze.id))) or 0

    return {
        "users": total_users,
        "lots": total_lots,
        "carriers": total_carriers,
        "boxes": total_boxes,
        "fuzes": total_fuzes
    }

