"""Add to ai_server/main.py:  from inspection.router import router as inspection_router ; app.include_router(inspection_router)"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from .registry import ModelRegistry
from .rules import load_config, evaluate, checklist, to_messages

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # ai_server/
CFG = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "models_config.yaml"))
registry = ModelRegistry(CFG, base_dir=BASE, max_loaded=int(os.getenv("MAX_LOADED_MODELS", "8")))
router = APIRouter(prefix="/inspect", tags=["inspection"])

# 3 Unified Component Stages
STAGE_MODELS = {
    "stage_carrier": ["carrier_seal_label", "carrier_rust"],
    "stage_box": ["h2a_seal_label", "h2a_rust", "h2a_inner", "primer_count"],
    "stage_primer": ["primer_assembly", "primer_paint"]
}


def resolve_model_keys(key: str):
    """Returns list of model keys for a unified stage, or a single model key."""
    if key in STAGE_MODELS:
        return STAGE_MODELS[key]
    if key in CFG:
        return [key]
    return []


def evaluate_frame_models(keys, frame, w, h):
    """Runs one or multiple RF-DETR models on a single frame and aggregates detections and checks."""
    all_dets = []
    all_checks = []
    overall = "PASS"

    for k in keys:
        if k in CFG:
            res = evaluate(CFG[k], registry.detect(k, frame))
            all_dets.extend(res.get("detections", []))
            all_checks.extend(res.get("checks", []))
            if res.get("overall") != "PASS":
                overall = "REJECT"

    msgs = [{"type": "detections", "frame_w": w, "frame_h": h, "detections": all_dets}]
    msgs += [{"type": "checklist", "id": c["id"], "status": c["status"]} for c in all_checks]
    return {"overall": overall, "messages": msgs, "checks": all_checks}


@router.get("/models")
def models():
    return [{"key": k, "stage": v["stage"], "checklist": checklist(v)} for k, v in CFG.items()]


@router.get("/{key}/checklist")
def get_checklist(key: str):
    keys = resolve_model_keys(key)
    if not keys:
        raise HTTPException(404, "unknown model or stage")
    cl = []
    for k in keys:
        cl.extend(checklist(CFG[k]))
    return cl


@router.post("/{key}")
async def inspect(key: str, image: UploadFile = File(...)):
    """Upload one frame -> messages for browser overlay (detections + checklist)."""
    keys = resolve_model_keys(key)
    if not keys:
        raise HTTPException(404, "unknown model or stage")

    import cv2, numpy as np
    frame = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "not an image")
    h, w = frame.shape[:2]
    return evaluate_frame_models(keys, frame, w, h)


@router.post("/{key}/video")
async def inspect_video(key: str, video: UploadFile = File(...), sample_fps: float = 1.0, max_frames: int = 150):
    """Upload a video file -> sample frames every N seconds -> run RF-DETR on each.
    Supports either an individual model key or one of the 3 unified stages:
      - stage_carrier (Seal + Rust)
      - stage_box (Seal + Rust + Inner Fitments + Count)
      - stage_primer (Assembly/Liner/Ring + Paint Peel)
    """
    keys = resolve_model_keys(key)
    if not keys:
        raise HTTPException(404, "unknown model or stage")

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
                res = evaluate_frame_models(keys, frame, w, h)
                timestamp_sec = round(frame_idx / video_fps, 2)

                if res.get("overall") != "PASS":
                    overall_verdict = "REJECT"

                # Downscale to max 960px wide to keep JSON payload manageable
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
                    "messages": res.get("messages", []),
                    "checks": res.get("checks", []),
                    "frame_image": frame_b64,
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
