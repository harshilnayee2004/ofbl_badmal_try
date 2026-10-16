from fastapi import Query
from typing import Optional
from core.database import get_db
from models.lot_model import Lot
from models.carrier_model import Carrier
from models.box_model import Box
from models.fuze_model import Fuze
from models.user_model import User
from sqlmodel import Session, select, func
from core.deps import get_current_user
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Depends, Request
from core.config import settings

router = APIRouter(prefix="/user", tags=["User"])
templates = Jinja2Templates(directory="templates")
templates.env.globals["settings"] = settings
templates.env.globals["is_dev"] = settings.IS_DEV

@router.get("/dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    carriers_count = db.scalar(select(func.count(Carrier.id)).where(Carrier.user_id == current_user.id, Carrier.carrier_inspection_status == 'Completed')) or 0
    boxes_count = db.scalar(select(func.count(Box.id)).where(Box.user_id == current_user.id, Box.box_inspection_status == 'Completed')) or 0
    fuzes_count = db.scalar(select(func.count(Fuze.id)).where(Fuze.user_id == current_user.id, Fuze.fuze_inspection_status == 'Completed')) or 0
    lots_count = db.scalar(select(func.count(Lot.id)).where(Lot.user_id == current_user.id)) or 0
    
    carrier_lots = db.exec(select(Lot).where(Lot.carrier_inspection_status.in_(['Pending', 'Inspecting']), (Lot.number_of_carrier > 0) | (Lot.carrier_type.isnot(None)))).all()
    box_lots = db.exec(select(Lot).where(Lot.box_inspection_status.in_(['Pending', 'Inspecting']))).all()
    fuze_lots = db.exec(select(Lot).where(Lot.primer_inspection_status.in_(['Pending', 'Inspecting']))).all()


    return templates.TemplateResponse(
        request=request,
        name="user/dashboard.html",
        context={
            "user": current_user,
            "carriers_count": carriers_count,
            "boxes_count": boxes_count,
            "fuzes_count": fuzes_count,
            "lots_count": lots_count,
            "carrier_lots": carrier_lots,
            "box_lots": box_lots,
            "fuze_lots": fuze_lots
        }
    )

@router.get("/manage_lots", response_class=HTMLResponse)
def manage_lots_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request,
        name="user/manage_lots.html",
        context={
            "user": current_user
        }
    )


@router.get("/count_boxes_and_primers", response_class=HTMLResponse)
@router.get("/count_boxes_and_fuzes", response_class=HTMLResponse)
def count_boxes_and_primers(
    request: Request,
    lot_id: Optional[int] = Query(None),
    count_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        request=request,
        name="user/count_boxes_primers.html",
        context={
            "user": current_user,
            "count_type": count_type,
            "lot_id": lot_id
        }
    )

count_boxes_and_fuzes = count_boxes_and_primers


@router.get("/inspect_carrier", response_class=HTMLResponse)
def inspect_carrier(
    request: Request,
    lot_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if lot_id is not None:
        return templates.TemplateResponse(
            request=request,
            name="user/inspect_carrier/inspection.html",
            context={
                "user": current_user,
                "lot_id": lot_id
            }
        )
    lots = db.exec(
        select(Lot).where(Lot.carrier_inspection_status.in_(["Pending", "Inspecting"]))
    ).all()
    
    return templates.TemplateResponse(
        request=request,
        name="user/inspect_carrier/selection.html",
        context={
            "user": current_user,
            "lot_id": lot_id if lot_id else "",
            "lots": lots
        }
    )


@router.get("/inspect_box", response_class=HTMLResponse)
def inspect_box(
    request: Request,
    lot_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if lot_id is not None:
        return templates.TemplateResponse(
            request=request,
            name="user/inspect_box/inspection.html",
            context={
                "user": current_user,
                "lot_id": lot_id,
                "is_dev": settings.IS_DEV
            }
        )
    lots = db.exec(
        select(Lot).where(Lot.box_inspection_status.in_(["Pending", "Inspecting"]))
    ).all()
    
    return templates.TemplateResponse(
        request=request,
        name="user/inspect_box/selection.html",
        context={
            "user": current_user,
            "lot_id": lot_id if lot_id else "",
            "lots": lots
        }
    )


@router.get("/inspect_primer", response_class=HTMLResponse)
@router.get("/inspect_fuze", response_class=HTMLResponse)
def inspect_primer(
    request: Request,
    lot_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if lot_id is not None:
        return templates.TemplateResponse(
            request=request,
            name="user/inspect_primer/inspection.html",
            context={
                "user": current_user,
                "lot_id": lot_id,
            }
        )
    lots = db.exec(
        select(Lot).where(Lot.primer_inspection_status.in_(["Pending", "Inspecting"]))
    ).all()
    return templates.TemplateResponse(
        request=request,
        name="user/inspect_primer/selection.html",
        context={
            "user": current_user,
            "lot_id": lot_id if lot_id else "",
            "lots": lots
        }
    )

inspect_fuze = inspect_primer