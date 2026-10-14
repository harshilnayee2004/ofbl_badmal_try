from sqlmodel import Session
from core.database import get_db
from services.lot_service import LotService
from schemas.response_dto import ResponseDTO
from fastapi import APIRouter, Depends, Query

router = APIRouter(
    prefix="/counting",
    tags=["Counting"]
)


@router.get("/start_m104_counting")
async def start_m104_counting(db: Session = Depends(get_db), lot_id: int = Query(None),
                   count_type: str = Query(None)):
    result = await LotService.start_counting(db=db, lot_id=lot_id, count_type=count_type)
    return ResponseDTO(message="Lots Fetched Successfully", status=True, object=result)