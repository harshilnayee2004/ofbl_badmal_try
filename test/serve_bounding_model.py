import io
import time
import numpy as np
import cv2
from PIL import Image
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from rfdetr import RFDETRSmall

# ==============================================================================
# SERVER CONFIGURATION
# ==============================================================================
HOST = "0.0.0.0"
PORT = 8000
MODEL_PATH = r"C:\Users\patel\Downloads\150-20260818T071537Z-1-001\150\checkpoint_best_total.pth"
CONFIDENCE = 0.60

CLASS_NAMES = [
    "0",
    "improper_assembly",
    "imporper_paper_liner",
    "proper_assembly",
    "proper_paper_liner",
    "rubber_present",
]
# ==============================================================================

app = FastAPI(title="RF-DETR Inference Server")

print("[INFO] Loading RF-DETR model...")
model = RFDETRSmall(
    pretrain_weights=MODEL_PATH,
    num_classes=len(CLASS_NAMES),
)
print("[INFO] Model loaded successfully on GPU/CUDA.")


@app.get("/")
def health_check():
    return {"status": "online", "model": "RFDETRSmall", "num_classes": len(CLASS_NAMES)}


@app.websocket("/ws/detect")
async def websocket_detect(websocket: WebSocket):
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "unknown"
    print(f"[WS] Client connected from {client_host}")

    try:
        while True:
            # Receive frame byte data (JPEG or raw image)
            data = await websocket.receive_bytes()
            if not data:
                continue

            t_start = time.perf_counter()

            # Decode image from buffer
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                await websocket.send_json({"detections": [], "inference_time_ms": 0.0})
                continue

            # Convert BGR OpenCV image to RGB PIL image for RF-DETR
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)

            # Perform inference
            results = model.predict(pil_image)
            inference_time_ms = (time.perf_counter() - t_start) * 1000.0

            # Filter detections and build response
            detections = []
            for box, score, label in zip(
                results.xyxy,
                results.confidence,
                results.class_id,
            ):
                score_val = float(score)
                if score_val < CONFIDENCE:
                    continue

                label_id = int(label)
                class_name = (
                    CLASS_NAMES[label_id]
                    if 0 <= label_id < len(CLASS_NAMES)
                    else str(label_id)
                )

                detections.append(
                    {
                        "box": [int(coord) for coord in box],
                        "score": round(score_val, 4),
                        "class_id": label_id,
                        "class_name": class_name,
                    }
                )

            # Send detection results back to client
            await websocket.send_json(
                {
                    "detections": detections,
                    "inference_time_ms": round(inference_time_ms, 2),
                }
            )

    except WebSocketDisconnect:
        print(f"[WS] Client {client_host} disconnected.")
    except Exception as e:
        print(f"[WS] Error during session with {client_host}: {e}")


if __name__ == "__main__":
    print(f"Starting RF-DETR Server on {HOST}:{PORT}...")
    uvicorn.run(app, host=HOST, port=PORT, ws_ping_interval=10, ws_ping_timeout=10)
