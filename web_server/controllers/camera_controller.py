from sqlmodel import Session
from core.database import get_db
from fastapi.responses import JSONResponse
from schemas.camera_dto import CameraUpdate
from schemas.response_dto import ResponseDTO
from services.camera_service import CameraService
from starlette.responses import StreamingResponse
from repositories.camera_repositories import CameraRepository
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from core.config import settings

api_router = APIRouter(prefix="/api/cameras", tags=["Cameras_API"])

# --- API Routes ---
@api_router.get("/suppress_error_status")
def get_suppress_error_status():
    return ResponseDTO(
        status=True,
        message="Camera error suppression status",
        object={
            "suppress_camera_error": CameraRepository.suppress_camera_error,
            "is_dev": settings.IS_DEV
        }
    )

@api_router.post("/toggle_suppress_error")
def toggle_suppress_error(enabled: Optional[bool] = Query(None)):
    if not settings.IS_DEV:
        CameraRepository.suppress_camera_error = False
        return ResponseDTO(
            status=False,
            message="Camera error suppression is only allowed in Development mode",
            object={"suppress_camera_error": False, "is_dev": False}
        )
    if enabled is not None:
        CameraRepository.suppress_camera_error = enabled
    else:
        CameraRepository.suppress_camera_error = not CameraRepository.suppress_camera_error
    return ResponseDTO(
        status=True,
        message="Camera error suppression updated",
        object={"suppress_camera_error": CameraRepository.suppress_camera_error, "is_dev": True}
    )

@api_router.get("/")
def get_all_cameras(db: Session = Depends(get_db)):
    cameras = CameraService.get_all_cameras(db)
    # Simple list for now, datatables can handle client-side or we can add pagination
    return {
        "data": cameras
    }

@api_router.put("/{camera_id}")
async def update_camera(camera_id: int, camera_data: CameraUpdate,request:Request, db: Session = Depends(get_db)):
    updated_camera = await CameraService.update_camera(db, camera_id, camera_data)
    if not updated_camera:
        return JSONResponse(status_code=404, content={"message": "Camera not found"})
    
    return ResponseDTO(
        status=True,
        message="Camera updated successfully",
        object=updated_camera
    )

@api_router.get("/stream/{position}")
async def stream_camera(position: str):
    position = position.upper()

    if position not in CameraRepository.stream_dict:
        raise HTTPException(status_code=404, detail="Invalid camera position")

    streaming_service = CameraRepository.stream_dict.get(position)

    # if not streaming_service:
    #     raise HTTPException(status_code=404, detail="Camera not initialized")

    return StreamingResponse(
        CameraService.mjpeg_frame_generator(streaming_service, position),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
        }
    )
