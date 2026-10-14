from schemas.response_schema import ResponseDTO
from fastapi import APIRouter, UploadFile, File, Form
from services.inspect_box_service import InspectBoxService

router = APIRouter(
    prefix="",
    tags=["Inspection"]
)

@router.post("/inspect_carrier/6al")
async def inspect_carrier_6al(
    carrier_id: int = Form(...),
    sequence_number: int = Form(...),
    lot_number: str = Form(...),
    image: UploadFile = File(...),
):
    result = await InspectBoxService.inspect_carrier_6al(carrier_id, sequence_number, image, lot_number)
    return ResponseDTO(
        message=f"Carrier 6A/L inspected for sequence number: {sequence_number}",
        status=True,
        object=result
    )

@router.post("/inspect_box/h2a")
async def inspect_box_h2a(
    box_id: int = Form(...),
    sequence_number: int = Form(...),
    lot_number: str = Form(...),
    image: UploadFile = File(...),
):
    result = await InspectBoxService.inspect_box_h2a(box_id, sequence_number, image, lot_number)
    return ResponseDTO(
        message=f"Box H2A inspected for sequence number: {sequence_number}",
        status=True,
        object=result
    )

# --- [LEGACY BOX G70 & M104 CONTROLLERS - PRESERVED] ---
# @router.post("/inspect_box/g70")
# async def inspect_box_g70(
#     box_id: int = Form(...),
#     sequence_number: int = Form(...),
#     lot_number: str = Form(...),
#     image: UploadFile = File(...),
# ):
#     result = await InspectBoxService.inspect_box_g70(box_id, sequence_number, image, lot_number)
#     return ResponseDTO(message=f"Started inspecting box G70: {sequence_number}", status=True, object=result)
#
# @router.post("/inspect_box/m104")
# async def inspect_box_m104(
#     box_id: int = Form(...),
#     sequence_number: int = Form(...),
#     lot_number: str = Form(...),
#     image: UploadFile = File(...),
# ):
#     result = await InspectBoxService.inspect_box_m104(box_id, sequence_number, image, lot_number)
#     return ResponseDTO(message=f"Started inspecting box M104: {sequence_number}", status=True, object=result)
