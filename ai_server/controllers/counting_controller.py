from schemas.response_schema import ResponseDTO
from fastapi import APIRouter, UploadFile, File, Form

from services.counting_service import CountingService
from services.inspect_box_service import InspectBoxService

router = APIRouter(
    prefix="/count",
    tags=["Count"]
)

@router.post("/C07")
async def count_container_c07(
    # box_id: int = Form(...),
    # sequence_number: int = Form(...),
    # lot_number: str = Form(...),
    image: UploadFile = File(...),
):

    # background_tasks.add_task(
    result = await CountingService.count_C07_container(image)

    return ResponseDTO(
        message=f"Count Completed Of C07 Containers",
        status=True,
        object=result
    )

@router.post("/M104")
async def count_box_m104(
    image: UploadFile = File(...),
):

    result = await CountingService.count_M104_box(image)

    return ResponseDTO(
        message=f"Count Completed Of M104 Boxes",
        status=True,
        object=result
    )