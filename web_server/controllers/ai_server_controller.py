import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from schemas.response_dto import ResponseDTO
from schemas.ai_server_dto import AiServerG70BoxRequest
from core.config import settings

router = APIRouter(
    prefix="/ai_server",
    tags=["AI Server"]
)


@router.post("/g70_box/inspection_result")
def g70_box(request: AiServerG70BoxRequest):
    return ResponseDTO(
        status=True,
        message="Inspection result received successfully",
        object=request
    )


@router.post("/inspect/{model_key}")
async def proxy_inspect(model_key: str, image: UploadFile = File(...)):
    """Proxies the browser inspection upload to the local AI Server without CORS issues."""
    ai_base_url = settings.AI_SERVER_URL.rstrip("/")
    target_url = f"{ai_base_url}/inspect/{model_key}"

    try:
        content = await image.read()
        files = {"image": (image.filename or "upload.jpg", content, image.content_type or "image/jpeg")}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(target_url, files=files)

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        return resp.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Server proxy error: {str(e)}")


@router.get("/inspect/{model_key}/checklist")
async def proxy_checklist(model_key: str):
    """Proxies checklist queries to AI server."""
    ai_base_url = settings.AI_SERVER_URL.rstrip("/")
    target_url = f"{ai_base_url}/inspect/{model_key}/checklist"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(target_url)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Server proxy error: {str(e)}")


@router.post("/inspect_video/{model_key}")
async def proxy_inspect_video(model_key: str, video: UploadFile = File(...), sample_fps: float = 2.0):
    """Proxies the browser video upload to the local AI Server without CORS issues."""
    ai_base_url = settings.AI_SERVER_URL.rstrip("/")
    target_url = f"{ai_base_url}/inspect/{model_key}/video?sample_fps={sample_fps}"

    try:
        content = await video.read()
        files = {"video": (video.filename or "upload.mp4", content, video.content_type or "video/mp4")}

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(target_url, files=files)

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        return resp.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Server video proxy error: {str(e)}")