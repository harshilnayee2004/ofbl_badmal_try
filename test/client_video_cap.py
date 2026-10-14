import os
import cv2
import time
import json
import asyncio
import threading
from datetime import datetime
import websockets
import numpy as np

# ==============================================================================
# CLIENT CONFIGURATION
# ==============================================================================
# Target PC GPU Server WebSocket URL (Replace with your server PC's LAN IP)
SERVER_WS_URL = "ws://192.168.1.100:8000/ws/detect"

# Sparsh CCTV RTSP Stream
RTSP_URL = "rtsp://admin:Mipl%40123@192.168.1.188:554/ch01.264"

# Frame Resolution & Transmission Quality
FRAME_W, FRAME_H = 1280, 960
JPEG_QUALITY = 80  # 1-100 (80 provides crisp detection with low network payload)

# Recording & Output Settings
RECORD_FPS = 15
OUTPUT_DIR = r"C:\Users\patel\OneDrive\Desktop\AI MIPL Primer\live_capture_outputs"
VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
IMAGE_DIR = os.path.join(OUTPUT_DIR, "snapshots")

# Bounding Box Display Settings
CONFIDENCE = 0.60

# Force TCP transport for RTSP stream stability
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
# ==============================================================================


class RTSPStreamReader:
    """
    Dedicated background thread for ingesting RTSP video.
    Prevents OpenCV internal buffer accumulation and delivers the freshest frame.
    """

    def __init__(self, rtsp_url, width=1280, height=960):
        self.rtsp_url = rtsp_url
        self.width = width
        self.height = height
        self.cap = None
        self.latest_frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.connected = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        return self

    def _open_capture(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.connected = self.cap.isOpened()
        return self.connected

    def _update_loop(self):
        while self.running:
            if not self.connected or self.cap is None or not self.cap.isOpened():
                print(f"[RTSP] Connecting to camera: {self.rtsp_url}...")
                if not self._open_capture():
                    print("[RTSP] Connection failed. Retrying in 2 seconds...")
                    time.sleep(2.0)
                    continue
                print("[RTSP] Camera connected successfully.")

            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("[RTSP] Failed to grab frame. Reconnecting...")
                self.connected = False
                time.sleep(0.5)
                continue

            # Resize if required
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))

            with self.lock:
                self.latest_frame = frame

        if self.cap:
            self.cap.release()

    def get_frame(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()


class InferenceClient:
    """
    Manages WebSocket communication with the PC GPU Server.
    Sends frames asynchronously and stores the latest detections thread-safely.
    """

    def __init__(self, server_url, jpeg_quality=80):
        self.server_url = server_url
        self.jpeg_quality = jpeg_quality
        self.latest_detections = []
        self.latest_inference_time_ms = 0.0
        self.server_connected = False
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.infer_fps = 0.0
        self.get_frame_fn = None

    def start(self, get_frame_fn):
        self.running = True
        self.get_frame_fn = get_frame_fn
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        return self

    def _run_async_loop(self):
        asyncio.run(self._client_loop())

    async def _client_loop(self):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        infer_count = 0
        fps_start = time.time()

        while self.running:
            try:
                print(f"[WS] Connecting to inference server: {self.server_url}...")
                async with websockets.connect(
                    self.server_url,
                    ping_interval=10,
                    ping_timeout=10,
                    max_size=10 * 1024 * 1024,
                ) as ws:
                    self.server_connected = True
                    print("[WS] Connected to inference server!")

                    while self.running:
                        frame = self.get_frame_fn()
                        if frame is None:
                            await asyncio.sleep(0.01)
                            continue

                        # Encode frame to JPEG
                        success, enc_buf = cv2.imencode(".jpg", frame, encode_param)
                        if not success:
                            await asyncio.sleep(0.01)
                            continue

                        send_t0 = time.perf_counter()

                        # Send frame bytes
                        await ws.send(enc_buf.tobytes())

                        # Receive detection JSON
                        raw_response = await ws.recv()
                        roundtrip_ms = (time.perf_counter() - send_t0) * 1000.0

                        try:
                            data = json.loads(raw_response)
                            detections = data.get("detections", [])
                            server_infer_ms = data.get("inference_time_ms", roundtrip_ms)

                            with self.lock:
                                self.latest_detections = detections
                                self.latest_inference_time_ms = server_infer_ms

                            infer_count += 1
                            elapsed = time.time() - fps_start
                            if elapsed >= 1.0:
                                self.infer_fps = infer_count / elapsed
                                infer_count = 0
                                fps_start = time.time()

                        except Exception as parse_err:
                            print(f"[WS] JSON parse error: {parse_err}")

            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError, OSError) as e:
                self.server_connected = False
                with self.lock:
                    self.latest_detections = []
                print(f"[WS] Connection error ({type(e).__name__}). Reconnecting in 2s...")
                await asyncio.sleep(2.0)
            except Exception as e:
                self.server_connected = False
                print(f"[WS] Unexpected error: {e}. Reconnecting in 2s...")
                await asyncio.sleep(2.0)

    def get_results(self):
        with self.lock:
            return (
                list(self.latest_detections),
                self.latest_inference_time_ms,
                self.server_connected,
                self.infer_fps,
            )

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)


def main():
    # Ensure output directories exist
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    print("==================================================")
    print("      Sparsh CCTV - Distributed RF-DETR Client    ")
    print("==================================================")
    print(f"RTSP Source   : {RTSP_URL}")
    print(f"Inference Host: {SERVER_WS_URL}")
    print(f"Resolution    : {FRAME_W}x{FRAME_H} @ {RECORD_FPS} FPS")
    print(f"Confidence Th : {CONFIDENCE}")  
    print("==================================================")

    # Initialize RTSP Stream Reader
    rtsp_reader = RTSPStreamReader(RTSP_URL, FRAME_W, FRAME_H).start()

    # Initialize Inference Client
    infer_client = InferenceClient(SERVER_WS_URL, JPEG_QUALITY).start(
        get_frame_fn=rtsp_reader.get_frame
    )

    # Setup Video Writer
    video_filename = os.path.join(
        VIDEO_DIR, f"sparsh_cctv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
    )
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video_writer = cv2.VideoWriter(
        video_filename, fourcc, RECORD_FPS, (FRAME_W, FRAME_H)
    )

    if not video_writer.isOpened():
        print("ERROR: VideoWriter failed to open. Check codec support.")
        rtsp_reader.stop()
        infer_client.stop()
        return

    WINDOW_NAME = "Sparsh CCTV - RF-DETR (Client)"
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    print(f"Recording session video to: {video_filename}")
    print("Controls: Press SPACE for snapshot | Press 'Q' to quit")
    print("==================================================")

    fps_start_time = time.time()
    fps_frame_count = 0
    display_fps = 0.0

    try:
        while True:
            frame = rtsp_reader.get_frame()

            if frame is None:
                blank_frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
                cv2.putText(
                    blank_frame,
                    "Connecting to Sparsh CCTV Stream...",
                    (int(FRAME_W / 4), int(FRAME_H / 2)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 165, 255),
                    2,
                )
                cv2.imshow(WINDOW_NAME, blank_frame)
                if cv2.waitKey(30) & 0xFF == ord("q"):
                    break
                continue

            display_frame = frame.copy()

            # Retrieve latest detections from server client
            (
                detections,
                infer_time_ms,
                server_connected,
                server_infer_fps,
            ) = infer_client.get_results()

            detection_count = 0

            # Draw Detections
            for det in detections:
                score = det.get("score", 0.0)
                if score < CONFIDENCE:
                    continue

                detection_count += 1
                x1, y1, x2, y2 = det.get("box", [0, 0, 0, 0])
                class_name = det.get("class_name", "object")
                text = f"{class_name}: {score:.2f}"

                # Bounding box
                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                # Text label
                cv2.putText(
                    display_frame,
                    text,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )

            # Calculate Local Processing FPS
            fps_frame_count += 1
            elapsed = time.time() - fps_start_time
            if elapsed >= 1.0:
                display_fps = fps_frame_count / elapsed
                fps_frame_count = 0
                fps_start_time = time.time()

            # Overlay HUD status
            conn_status = "SERVER: CONNECTED" if server_connected else "SERVER: OFFLINE (Reconnecting...)"
            conn_color = (0, 255, 0) if server_connected else (0, 0, 255)

            cv2.putText(
                display_frame,
                conn_status,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                conn_color,
                2,
            )
            cv2.putText(
                display_frame,
                f"Processing FPS: {display_fps:.1f}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 0),
                2,
            )
            cv2.putText(
                display_frame,
                f"Inference FPS: {server_infer_fps:.1f} ({infer_time_ms:.1f}ms)",
                (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 0),
                2,
            )
            cv2.putText(
                display_frame,
                f"Detections: {detection_count}",
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 0),
                2,
            )

            # Write annotated frame to session video
            video_writer.write(display_frame)

            # Show live window
            cv2.imshow(WINDOW_NAME, display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" "):
                snapshot_name = os.path.join(
                    IMAGE_DIR,
                    f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg",
                )
                cv2.imwrite(snapshot_name, display_frame)
                print(f"Snapshot saved: {snapshot_name}")

    finally:
        print("\nShutting down client...")
        rtsp_reader.stop()
        infer_client.stop()
        video_writer.release()
        cv2.destroyAllWindows()

        print(f"Session video saved to: {video_filename}")
        print(f"Snapshots folder: {IMAGE_DIR}")


if __name__ == "__main__":
    main()
