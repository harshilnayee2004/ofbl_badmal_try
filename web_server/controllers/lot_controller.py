from sqlmodel import Session
from core.database import get_db
from models.user_model import User
from schemas.lot_dto import LotCreate
from core.deps import get_current_user
from services.lot_service import LotService
from schemas.response_dto import ResponseDTO
from fastapi import APIRouter, Depends, Query

router = APIRouter(
    prefix="/lots",
    tags=["Lots"]
)

@router.post("/create")
async def create_lot(
        lot_data: LotCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = await LotService.create_lot(db, lot_data, current_user.id, current_user.email)
    return ResponseDTO(message="Lot Created Successfully", status=True, object=result)

@router.get("/")
@router.get("/get_all_lots")
def get_lots(db: Session = Depends(get_db)):
    result = LotService.get_all_lots(db)
    return ResponseDTO(message="Lots Fetched Successfully", status=True, object=result)

@router.get("/get_lots_for_inspection")
def get_lots_for_inspection(db: Session = Depends(get_db), inspection_type: str = Query(None)):
    result = LotService.get_lots_for_inspection(db, inspection_type)
    return ResponseDTO(message="Lots Fetched Successfully", status=True, object=result)

@router.get("/get_lot_by_id/{lot_id}")
def get_lot_by_id(lot_id: int, db: Session = Depends(get_db)):
    result = LotService.get_lot_by_id(db, lot_id)
    return ResponseDTO(message="Lots Fetched Successfully", status=True, object=result)

@router.get("/search")
def search_lots(query: str, db: Session = Depends(get_db)):
    result = LotService.search_lots(db, query)
    return ResponseDTO(message="Lots Searched Successfully", status=True, object=result)

@router.post("/increment_carrier_sequence/{lot_id}")
async def increment_carrier_sequence(
        lot_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = LotService.increment_carrier_sequence(db, lot_id)
    return ResponseDTO(message=result.get('message'), status=result.get('status'), object=None)

@router.post("/decrement_carrier_sequence/{lot_id}")
async def decrement_carrier_sequence(
        lot_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = LotService.decrement_carrier_sequence(db, lot_id)
    return ResponseDTO(message=result.get('message'), status=result.get('status'), object=None)

@router.post("/increment_box_sequence/{lot_id}")
async def increment_box_sequence(
        lot_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = LotService.increment_box_sequence(db, lot_id)
    return ResponseDTO(message=result.get('message'), status=result.get('status'), object=None)

@router.post("/decrement_box_sequence/{lot_id}")
async def decrement_box_sequence(
        lot_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    LotService.decrement_box_sequence(db, lot_id)
    return ResponseDTO(message="Sequence Updated", status=True, object=None)

@router.post("/increment_primer_sequence/{box_id}")
@router.post("/increment_fuze_sequence/{box_id}")
async def increment_fuze_sequence(
        box_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = LotService.increment_fuze_sequence(db, box_id)
    return ResponseDTO(message=result["message"], status=result["status"], object=None)

@router.post("/decrement_primer_sequence/{lot_id}")
@router.post("/decrement_fuze_sequence/{lot_id}")
async def decrement_fuze_sequence(
        lot_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    LotService.decrement_fuze_sequence(db, lot_id)
    return ResponseDTO(message="Sequence Updated", status=True, object=None)

@router.get("/get_count_information")
def get_count_information(db: Session = Depends(get_db), lot_id: int = Query(None),
                                 count_type: str = Query(None)):
    result = LotService.get_count_information(db=db, lot_id=lot_id, count_type=count_type)
    return ResponseDTO(message="Lots Fetched Successfully", status=True, object=result)

@router.get("/get_primer_by_lot_id/{lot_id}")
@router.get("/get_fuze_by_lot_id/{lot_id}")
def get_fuze_by_lot_id(lot_id: int, db: Session = Depends(get_db)):
    result = LotService.get_fuze_by_lot_id(db, lot_id)
    return ResponseDTO(message="Primers Fetched Successfully", status=True, object=result)

@router.get("/get_box_by_lot_id/{lot_id}")
def get_box_by_lot_id(lot_id: int, db: Session = Depends(get_db)):
    result = LotService.get_box_by_lot_id(db, lot_id)
    return ResponseDTO(message="Boxes Fetched Successfully", status=True, object=result)

@router.get("/get_box_for_primer_reference/{lot_id}")
@router.get("/get_box_for_fuze_reference/{lot_id}")
def get_box_for_fuze_reference(lot_id: int, db: Session = Depends(get_db)):
    result = LotService.get_box_for_fuze_reference(db, lot_id)
    return ResponseDTO(message="Boxes Fetched Successfully", status=True, object=result)

@router.post("/update_acceptance_status/{lot_id}")
async def update_lot_acceptance_status(
        lot_id: int,
        status: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = LotService.update_lot_acceptance_status(db, lot_id, status)
    return ResponseDTO(message=result.get('message'), status=result.get('status'), object=None)