from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from core.database import get_db
from models.lot_model import Lot
from models.user_model import User
from core.deps import get_current_user
from schemas.inspection_dto import InspectionDetailsRequestDTO
from schemas.response_dto import ResponseDTO
from services.lot_service import LotService
from typing import List, Dict, Any
import datetime

router = APIRouter(
    prefix="/inspections",
    tags=["Inspections"]
)


@router.post("/get_inspection_details")
def get_inspection_details(request:InspectionDetailsRequestDTO,db: Session = Depends(get_db)):
    result=InspectionService.get_inspection_details(db,request.lot_id,request.box_type)
    return ResponseDTO(message="Lots Fetched Successfully",status=True,object=result)