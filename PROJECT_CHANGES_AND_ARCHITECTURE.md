# OFBL Badmal — Complete Implementation & Changes Changelog
### MIPL (Maharashtra Instrument Pvt Ltd) · AI Inspection System

This document contains a comprehensive record of all features, architecture components, bug fixes, and code modifications implemented in this project.

---

## 📌 Executive Summary

The **OFBL Badmal AI Ammunition Inspection System** is designed to replace manual visual inspection of ordnance units (Primers, Boxes, Fuzes, Carriers) with deep learning RF-DETR computer vision models.

Because the physical factory CCTV cameras are currently being wired and installed on the shop floor, **a complete Video & Image Inspection Sandbox** was designed, developed, and deployed. This enables operators and inspecting officers to upload inspection videos (or select built-in sample videos) to simulate live camera detection in real time.

---

## 🛠️ Complete List of Added & Modified Files

### 1. Backend AI Engine (`ai_server/`)
* **[`ai_server/inspection/router.py`](file:///c:/MIPL/AI_Badmal_backup%20(2)/AI_Badmal_backup/ai_server/inspection/router.py)**:
  * **New Endpoint**: `POST /inspect/{key}/video`:
    * Accepts uploaded video files (`.mp4`, `.avi`, `.mov`, `.mkv`, etc.).
    * Safely writes video to a temporary file and opens via OpenCV `cv2.VideoCapture`.
    * Samples frames at a configurable rate (default: `1.0 FPS` = 1 frame per second).
    * Evaluates each sampled frame against the selected RF-DETR model (`primer_assembly`, `h2a_rust`, etc.).
    * **Visual Evidence Extraction**: Encodes each sampled frame as a downscaled (max 960px width) base64 JPEG (`frame_image`) and attaches original resolution dimensions (`frame_w`, `frame_h`).
    * Returns full inspection verdict (`PASS` / `REJECT`), total frames, sampled frames count, and per-frame detection boxes with checklist results.

### 2. Web Application Backend (`web_server/`)
* **[`web_server/controllers/ai_server_controller.py`](file:///c:/MIPL/AI_Badmal_backup%20(2)/AI_Badmal_backup/web_server/controllers/ai_server_controller.py)**:
  * Added reverse proxy endpoints to route browser inspection requests to the AI server without CORS restrictions:
    * `POST /ai_server/inspect/{model_key}`: Proxies single frame / image inspection.
    * `POST /ai_server/inspect_video/{model_key}`: Proxies video file stream and batch inspection with extended timeout (180s).
* **[`web_server/.gitignore`](file:///c:/MIPL/AI_Badmal_backup%20(2)/AI_Badmal_backup/web_server/.gitignore)**:
  * Added `*.db` and `badmal_dev.db` to prevent committing local SQLite binaries to GitHub.

### 3. User Interface & Modals (`web_server/templates/`)
* **[`web_server/templates/shared/ai_sandbox_modals.html`](file:///c:/MIPL/AI_Badmal_backup%20(2)/AI_Badmal_backup/web_server/templates/shared/ai_sandbox_modals.html)**:
  * **Image Sandbox Modal (`#uploadTestModal`)**:
    * Model selector dropdown (7 RF-DETR ordnance models).
    * Drag & drop image zone.
    * Canvas with dynamic colored bounding boxes (Green = Pass, Red = Defect).
    * Live criteria checklist and detections table with confidence scores.
  * **Video Sandbox Modal (`#videoTestModal`)**:
    * Visible `<video id="hiddenTestVideo">` with playback controls.
    * Overlay `<canvas id="videoResultCanvas">` perfectly aligned over the video stream.
    * Sample rate selector dropdown (1 FPS default, 2 FPS, 3 FPS, 5 FPS).
    * **Sample Videos Dropdown**: One-click loading of verified working factory videos (`Primer 1A/L Sample` and `Box H2A Sample`).
    * **Browser Playback Notice Banner**: Detects unplayable raw CCTV or corrupted MP4 headers and offers a 1-click fallback to the Full Server Scan.
    * **Interactive Server Scan Frame Viewer**:
      * Header summary bar (Batch Verdict, total frames, sampled frames, defect count).
      * Left viewport: Canvas displaying the exact frame image with scaled bounding boxes.
      * Prev / Next frame navigation controls (`< Prev`, `Next >`, and frame counter).
      * Right sidebar: Scrollable list of all sampled frames with defect badges and timestamps. Clicking any frame jumps the viewer directly to that frame.
      * Criteria checklist breakdown for the selected frame.
* **[`web_server/templates/admin/surveillance.html`](file:///c:/MIPL/AI_Badmal_backup%20(2)/AI_Badmal_backup/web_server/templates/admin/surveillance.html)** & **[`web_server/templates/surveillance/dashboard.html`](file:///c:/MIPL/AI_Badmal_backup%20(2)/AI_Badmal_backup/web_server/templates/surveillance/dashboard.html)**:
  * Integrated "Upload & Test Video" and "Upload & Test Image" action buttons into surveillance headers.
  * Included `ai_sandbox_modals.html` and loaded `ai_sandbox.js`.

### 4. Client-Side Video & AI Testing Engine (`web_server/static/js/`)
* **[`web_server/static/js/ai_sandbox.js`](file:///c:/MIPL/AI_Badmal_backup%20(2)/AI_Badmal_backup/web_server/static/js/ai_sandbox.js)**:
  * **Continuous Real-Time Playback Engine**:
    * Video plays smoothly at normal 1.0x playback speed without pauses.
    * Uses `requestAnimationFrame(runContinuousVideoLoop)` to keep the overlay canvas and timeline progress bar synced.
  * **Periodic 1-Second Snapshot Sampling**:
    * Every 1 second (1000ms), an offscreen canvas captures the current frame snapshot via `offCtx.drawImage(videoElement, ...)`.
    * Sends the snapshot blob to `/ai_server/inspect/{model_key}`.
    * Guarded with `isProcessingFrame` flag to prevent request congestion when an inference is in-flight.
    * Updates the real-time decision card (`ACCEPTED (PASS)` / `DEFECT DETECTED (REJECT)`), checklist items, and bounding box overlay.
  * **Frame Viewer & Timeline Navigation**:
    * `runServerVideoScan()`: Triggers full OpenCV scan on the server, stores results, and populates the frame list.
    * `jumpToFrame(idx)`: Loads selected frame into canvas with scaled bounding boxes and criteria checklist.
    * `navigateFrame(delta)`: Prev/Next arrow navigation.
  * **Error Handling & Sample Loading**:
    * `loadSampleVideo(url, name)`: Fetches local sample video blobs and loads them into the player.
    * `videoElement.onerror`: Detects browser decode failures and displays the Server Scan notice.

### 5. Verified Factory Sample Media (`web_server/static/sample_videos/`)
* `primer_inspection_sample.mp4` (21.7 MB): Verified inspection video of Primer Electric 1A/L on rotary jig.
* `box_inspection_sample.mp4` (27.8 MB): Verified inspection video of H2A Explosive Box showing seals, markings, and rust inspection.

---

## 🔍 Key Problems Identified & Solutions Implemented

| Problem Encountered | Technical Root Cause | Solution Implemented |
|---|---|---|
| **Raw CCTV / Interrupted Video Won't Play in Browser** | File `inspection_video.mp4` had missing `moov` atom / corrupted H.264 NAL headers from recording interruption. Chrome HTML5 `<video>` threw `MEDIA_ERR_SRC_NOT_SUPPORTED`. | Added OpenCV server-side decoding fallback (`POST /ai_server/inspect_video/...`). OpenCV reads raw streams regardless of browser codec support. Also added a built-in "Sample Videos" dropdown. |
| **Server Scan Returned Only Text** | Server scan reported timestamps and defect frame numbers, but the officer could not visually inspect what was detected. | Updated `router.py` to encode each sampled frame as base64 JPEG (`frame_image`) and added a visual **Frame Viewer** with canvas bounding boxes and interactive frame timeline. |
| **Video Playback Lag / Mismatch** | AI inference takes ~2.5–3.0s per frame, while video plays at 30fps. If sampled too fast (e.g. 5 FPS), bounding boxes lagged 3 seconds behind the video. | 1. Implemented **Step-by-Step Seek Mode** where the video walks frame-by-frame.<br>2. Updated to **Continuous Playback Mode** with controlled 1-second periodic snapshot sampling that never blocks video playback. |
| **Port Conflicts on Startup** | Port 8000 was already bound by an existing zombie process (`[Errno 10048]`). | Terminated conflicting process via PID kill and restarted AI server on 8000 and Web server on 8080. |
| **Variable Rededeclaration Error** | Duplicate `let videoFrameCount = 0;` caused syntax error during script initialization. | Removed duplicate declaration; verified with `node -c` (exit code 0). |

---

## 📦 Git Commits Pushed to GitHub

All changes are committed and pushed to [harshilnayee2004/ofbl_badmal_try](https://github.com/harshilnayee2004/ofbl_badmal_try) on branch `main`:

1. `20b8ab2` — *Add video upload inspection and AI testing sandbox*
2. `017e295` — *Enhance video sandbox with visible video player, overlay canvas, error fallbacks, and server scan*
3. `ad08299` — *Add sample videos dropdown and browser fallback to server scan*
4. `b07d8cc` — *feat: video frame viewer — return base64 JPEG per frame + render with bounding boxes in UI*
5. `160b2ff` — *fix: set default frame capture to 1 FPS (1 frame per second) across video scan and UI*
6. `7918fc5` — *feat: replace live-loop with step-by-step seek mode — seek→capture→AI→show→advance, no lag*
7. `9ba7e45` — *fix: remove duplicate videoFrameCount declaration in ai_sandbox.js*
8. `ca2eb9a` — *feat: continuous real-time video playback without pause with 1s periodic snapshot sampling*

---

## 🚦 System Operating Ports

- **AI Inference Engine (FastAPI + RF-DETR)**: `http://127.0.0.1:8000` (Swagger docs at `/docs`)
- **Web Application & UI (FastAPI + Jinja2)**: `http://127.0.0.1:8080` (Surveillance feed at `/admin/surveillance` or `/surveillance/`)
