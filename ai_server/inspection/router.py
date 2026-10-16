"""Add to ai_server/main.py:  from inspection.router import router as inspection_router ; app.include_router(inspection_router)"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from .registry import ModelRegistry
from .rules import load_config, evaluate, checklist, to_messages
from .ocr_service import run_carrier_text_ocr, run_box_text_ocr, run_primer_text_ocr

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # ai_server/
CFG = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "models_config.yaml"))
registry = ModelRegistry(CFG, base_dir=BASE, max_loaded=int(os.getenv("MAX_LOADED_MODELS", "8")))
router = APIRouter(prefix="/inspect", tags=["inspection"])

# Unified Component Stages (Split Box into Outside and Inside)
STAGE_MODELS = {
    "stage_carrier": ["carrier_seal_label", "carrier_rust"],
    "stage_box_outer": ["h2a_seal_label", "h2a_rust"],
    "stage_box_inner": ["h2a_inner", "primer_count"],
    "stage_box": ["h2a_seal_label", "h2a_rust", "h2a_inner", "primer_count"],  # retained for backwards compatibility
    "stage_primer": ["primer_assembly", "primer_paint"]
}

OCR_CHECKLIST_MAP = {
    "carrier_text": [
        {"id": "carrier_stencil_av_mass", "label": "Horizontal stencil: AV MASS KG-40.800"},
        {"id": "carrier_stencil_lot", "label": "Carrier Lot / BL stencil format"},
        {"id": "carrier_stencil_no", "label": "Carrier unit serial number"}
    ],
    "box_text": [
        {"id": "box_stencil_primelec", "label": "Box stencil text: PRIMELEC1A"},
        {"id": "box_stencil_no", "label": "Box unit number"}
    ],
    "primer_text": [
        {"id": "primer_stencil_read", "label": "Primer 1A/L micro-stencil fields recognized"}
    ]
}

STAGE_OCR_MAP = {
    "stage_carrier": "carrier_text",
    "stage_box_outer": "box_text",
    "stage_primer": "primer_text"
}


def resolve_model_keys(key: str):
    """Returns list of model keys for a unified stage, or a single model key."""
    if key in STAGE_MODELS:
        return STAGE_MODELS[key]
    if key in CFG:
        return [key]
    if key in OCR_CHECKLIST_MAP:
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
    res = [{"key": k, "stage": v["stage"], "checklist": checklist(v)} for k, v in CFG.items()]
    res.append({"key": "carrier_text", "stage": "carrier", "checklist": OCR_CHECKLIST_MAP["carrier_text"]})
    res.append({"key": "box_text", "stage": "box", "checklist": OCR_CHECKLIST_MAP["box_text"]})
    res.append({"key": "primer_text", "stage": "primer", "checklist": OCR_CHECKLIST_MAP["primer_text"]})
    return res


@router.get("/{key}/checklist")
def get_checklist(key: str):
    if key in OCR_CHECKLIST_MAP:
        return OCR_CHECKLIST_MAP[key]
    keys = resolve_model_keys(key)
    if not keys:
        raise HTTPException(404, "unknown model or stage")
    cl = []
    for k in keys:
        if k in CFG:
            cl.extend(checklist(CFG[k]))
        elif k in OCR_CHECKLIST_MAP:
            cl.extend(OCR_CHECKLIST_MAP[k])
    if key in STAGE_OCR_MAP and STAGE_OCR_MAP[key] in OCR_CHECKLIST_MAP:
        cl.extend(OCR_CHECKLIST_MAP[STAGE_OCR_MAP[key]])
    return cl


@router.post("/{key}")
async def inspect(key: str, image: UploadFile = File(...)):
    """Upload one frame -> messages for browser overlay (detections + checklist + OCR data)."""
    import cv2, numpy as np

    image_bytes = await image.read()
    frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "not an image")
    h, w = frame.shape[:2]

    # 1. Pure OCR Inspection
    if key in OCR_CHECKLIST_MAP:
        if key == "carrier_text":
            ocr_res = await run_carrier_text_ocr(image_bytes, image.filename or "frame.jpg")
        elif key == "box_text":
            ocr_res = await run_box_text_ocr(image_bytes, image.filename or "frame.jpg")
        elif key == "primer_text":
            ocr_res = await run_primer_text_ocr(image_bytes, image.filename or "frame.jpg")
        else:
            raise HTTPException(404, "unknown OCR model")

        return {
            "overall": ocr_res["overall"],
            "messages": [
                {"type": "detections", "frame_w": w, "frame_h": h, "detections": []},
                *[{"type": "checklist", "id": c["id"], "status": c["status"]} for c in ocr_res["checks"]]
            ],
            "checks": ocr_res["checks"],
            "ocr_data": ocr_res["ocr_data"]
        }

    keys = resolve_model_keys(key)
    if not keys:
        raise HTTPException(404, "unknown model or stage")

    # 2. Visual Object Detection (RF-DETR)
    res = evaluate_frame_models(keys, frame, w, h)

    # 3. If Unified Stage has OCR, run it concurrently/sequentially
    if key in STAGE_OCR_MAP:
        ocr_key = STAGE_OCR_MAP[key]
        try:
            if ocr_key == "carrier_text":
                ocr_res = await run_carrier_text_ocr(image_bytes, image.filename or "frame.jpg")
            elif ocr_key == "box_text":
                ocr_res = await run_box_text_ocr(image_bytes, image.filename or "frame.jpg")
            elif ocr_key == "primer_text":
                ocr_res = await run_primer_text_ocr(image_bytes, image.filename or "frame.jpg")
            else:
                ocr_res = None

            if ocr_res:
                res["checks"].extend(ocr_res["checks"])
                res["messages"].extend([{"type": "checklist", "id": c["id"], "status": c["status"]} for c in ocr_res["checks"]])
                res["ocr_data"] = ocr_res["ocr_data"]
                if ocr_res["overall"] != "PASS":
                    res["overall"] = "REJECT"
        except Exception as ocr_err:
            print(f"[Warning] Stage OCR error for {key}: {ocr_err}")

    return res


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
