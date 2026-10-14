import cv2
import os
import time
from datetime import datetime
from PIL import Image
from rfdetr import RFDETRSmall


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

model = RFDETRSmall(
    pretrain_weights=MODEL_PATH,
    num_classes=6,
)


OUTPUT_DIR = r"C:\Users\patel\OneDrive\Desktop\AI MIPL Primer\live_capture_outputs"

VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
IMAGE_DIR = os.path.join(OUTPUT_DIR, "snapshots")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)


RTSP_URL = "rtsp://admin:Mipl%40123@192.168.1.188:554/ch01.264"

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("ERROR: Cannot open Sparsh CCTV")
    exit()


FRAME_W, FRAME_H = 1280, 960

FPS = 15

video_filename = os.path.join(
    VIDEO_DIR,
    f"sparsh_cctv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
)

fourcc = cv2.VideoWriter_fourcc(*"XVID")

video_writer = cv2.VideoWriter(
    video_filename,
    fourcc,
    FPS,
    (FRAME_W, FRAME_H)
)

if not video_writer.isOpened():
    print("ERROR: VideoWriter failed to open - check codec support")
    cap.release()
    exit()


WINDOW_NAME = "Sparsh CCTV - RF-DETR"

cv2.namedWindow(
    WINDOW_NAME,
    cv2.WINDOW_NORMAL
)


print("====================================")
print("Sparsh CCTV connected")
print("Starting live RF-DETR detection...")
print(f"Recording session video to: {video_filename}")
print("Press SPACE to save a snapshot")
print("Press Q to quit")
print("====================================")


fps_start_time = time.time()
fps_frame_count = 0
display_fps = 0.0


try:

    while True:

        ret, frame = cap.read()

        if not ret:

            print("Frame read failed")

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            time.sleep(0.05)

            continue


        frame = cv2.resize(
            frame,
            (FRAME_W, FRAME_H)
        )

        display_frame = frame.copy()


        image = Image.fromarray(
            cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )
        )


        inference_start = time.time()

        results = model.predict(image)

        inference_time = time.time() - inference_start

        inference_fps = 1.0 / inference_time if inference_time > 0 else 0


        detection_count = 0


        for box, score, label in zip(
            results.xyxy,
            results.confidence,
            results.class_id
        ):

            score = float(score)

            if score < CONFIDENCE:
                continue

            detection_count += 1

            x1, y1, x2, y2 = map(
                int,
                box
            )

            label_id = int(label)

            if 0 <= label_id < len(CLASS_NAMES):
                class_name = CLASS_NAMES[label_id]
            else:
                class_name = str(label_id)

            text = f"{class_name}: {score:.2f}"


            cv2.rectangle(
                display_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )


            cv2.putText(
                display_frame,
                text,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )


        fps_frame_count += 1

        elapsed = time.time() - fps_start_time

        if elapsed >= 1.0:

            display_fps = fps_frame_count / elapsed

            fps_frame_count = 0
            fps_start_time = time.time()


        cv2.putText(
            display_frame,
            f"Processing FPS: {display_fps:.1f}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )

        cv2.putText(
            display_frame,
            f"Inference FPS: {inference_fps:.1f}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )

        cv2.putText(
            display_frame,
            f"Detections: {detection_count}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )


        video_writer.write(
            display_frame
        )


        cv2.imshow(
            WINDOW_NAME,
            display_frame
        )


        key = cv2.waitKey(1) & 0xFF


        if key == ord("q"):
            break


        elif key == ord(" "):

            snapshot_name = os.path.join(
                IMAGE_DIR,
                f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            )

            cv2.imwrite(
                snapshot_name,
                display_frame
            )

            print(
                f"Snapshot saved: {snapshot_name}"
            )


finally:

    cap.release()

    video_writer.release()

    cv2.destroyAllWindows()

    print()
    print(
        f"Session video saved to: {video_filename}"
    )
    print(
        f"Snapshots folder: {IMAGE_DIR}"
    )
    print()