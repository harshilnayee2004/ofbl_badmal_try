"""Add to ai_server/main.py:  from inspection.router import router as inspection_router ; app.include_router(inspection_router)"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from .registry import ModelRegistry
from .rules import load_config, evaluate, checklist, to_messages

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # ai_server/
CFG = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "models_config.yaml"))
registry = ModelRegistry(CFG, base_dir=BASE, max_loaded=int(os.getenv("MAX_LOADED_MODELS", "2")))
router = APIRouter(prefix="/inspect", tags=["inspection"])


@router.get("/models")
def models():
    return [{"key": k, "stage": v["stage"], "checklist": checklist(v)} for k, v in CFG.items()]


@router.get("/{key}/checklist")
def get_checklist(key: str):
    if key not in CFG:
        raise HTTPException(404, "unknown model")
    return checklist(CFG[key])


@router.post("/{key}")
async def inspect(key: str, image: UploadFile = File(...)):
    """Upload one frame -> messages for the browser overlay (detections + checklist)."""
    if key not in CFG:
        raise HTTPException(404, "unknown model")
    import cv2, numpy as np
    frame = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "not an image")
    h, w = frame.shape[:2]
    result = evaluate(CFG[key], registry.detect(key, frame))
    return {"overall": result["overall"], "messages": to_messages(result, w, h), "checks": result["checks"]}


@router.post("/{key}/video")
async def inspect_video(key: str, video: UploadFile = File(...), sample_fps: float = 2.0, max_frames: int = 150):
    """Upload a video file -> sample frames every N seconds -> run RF-DETR on each.
    Each sampled result includes:
      - frame_image: base64 JPEG of the actual captured frame (browser renders this)
      - messages: bounding box detections with pixel coords
      - checks: pass/fail per criteria
      - overall: PASS or REJECT for that frame
    """
    if key not in CFG:
        raise HTTPException(404, "unknown model")
    import cv2, tempfile, base64

    suffix = os.path.splitext(video.filename or ".mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await video.read())
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise HTTPException(400, "Could not open video file. Invalid or unsupported format.")

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        step = max(1, int(round(video_fps / max(0.5, sample_fps))))

        frame_idx = 0
        sampled_results = []
        overall_verdict = "PASS"

        while cap.isOpened() and len(sampled_results) < max_frames:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if frame_idx % step == 0:
                h, w = frame.shape[:2]
                res = evaluate(CFG[key], registry.detect(key, frame))
                timestamp_sec = round(frame_idx / video_fps, 2)

                if res.get("overall") != "PASS":
                    overall_verdict = "REJECT"

                # Encode frame as base64 JPEG so the browser can render it visually.
                # Downscale to max 960px wide to keep JSON payload manageable.
                thumb = frame
                max_w = 960
                if w > max_w:
                    scale = max_w / w
                    thumb = cv2.resize(frame, (max_w, int(h * scale)), interpolation=cv2.INTER_AREA)
                encode_ok, buf = cv2.imencode(".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, 65])
                frame_b64 = base64.b64encode(buf.tobytes()).decode("utf-8") if encode_ok else None

                sampled_results.append({
                    "frame_index": frame_idx,
                    "timestamp": timestamp_sec,
                    "overall": res.get("overall"),
                    "messages": to_messages(res, w, h),
                    "checks": res.get("checks", []),
                    "frame_image": frame_b64,   # base64 JPEG — browser draws boxes on top of this
                    "frame_w": w,
                    "frame_h": h,
                })

            frame_idx += 1

        cap.release()
        return {
            "overall": overall_verdict,
            "total_frames_in_video": total_frames,
            "sampled_frames_count": len(sampled_results),
            "video_fps": round(video_fps, 2),
            "sampled_results": sampled_results
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
