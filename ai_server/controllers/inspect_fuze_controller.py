from services.inspect_fuze_service import InspectFuzeService
from fastapi import APIRouter, UploadFile, File, Form
from schemas.response_schema import ResponseDTO

router = APIRouter(
    prefix="",
    tags=["Inspection"]
)

@router.post("/inspect_fuze/primer_1al")
async def inspect_primer_1al(
    fuze_id: int = Form(...),
    sequence_number: int = Form(...),
    lot_number: str = Form(...),
    image: UploadFile = File(...),
):
    result = await InspectFuzeService.inspect_primer_1al(fuze_id, sequence_number, image, lot_number)
    return ResponseDTO(
        message=f"Primer Electric 1A/L inspected for sequence number: {sequence_number}",
        status=True,
        object=result
    )