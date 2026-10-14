import cv2
import numpy as np
import datetime
import asyncio
import os
import subprocess
from repositories.camera_repositories import CameraRepository


class VideoRecorder:
    def __init__(self, output_dir, lot_number, inspection_type,first_stream,second_stream,box_number=None):
        self.output_path = os.path.join(output_dir, "inspection_video.mp4")
        self.lot_number = lot_number
        self.inspection_type = inspection_type
        self.box_number = box_number
        self.first_stream = first_stream
        self.second_stream = second_stream
        self.fps = 10
        self.width = 1280
        self.height = 480
        self.top_padding = 60
        self.bottom_padding = 60

        self.total_height = self.height + self.top_padding + self.bottom_padding
        self.total_width = self.width

        self.process = None
        self.is_recording = False
        self.task = None

    async def start(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        ffmpeg_cmd = [
            "ffmpeg",
            "-loglevel", "error",
            "-y",

            # Input
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self.total_width}x{self.total_height}",
            "-r", str(self.fps),
            "-i", "-",

            # Encoding (CPU)
            "-c:v", "libx264",
            "-preset", "veryfast",          # good CPU balance
            "-tune", "zerolatency",         # better streaming behavior
            "-profile:v", "baseline",       # max compatibility
            "-level", "3.0",
            "-pix_fmt", "yuv420p",          # REQUIRED for browsers
            "-g", str(self.fps * 2),        # keyframe interval
            "-bf", "0",                     # disable B-frames (important for compatibility)

            # Bitrate control
            "-crf", "23",                   # good quality
            "-maxrate", "2M",
            "-bufsize", "4M",

            # Web optimization
            "-movflags", "+faststart",

            self.output_path
        ]

        try:
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if self.process.poll() is not None:
                print("[REC Warning] FFmpeg process exited immediately. Recording skipped.")
                self.process = None
                return

            self.is_recording = True
            self.task = asyncio.create_task(self.record_loop())
            print(f"[REC] Video recording started: {self.output_path}")
        except FileNotFoundError:
            print(f"[REC Warning] FFmpeg executable not found in PATH. Video recording skipped (Dev Mode).")
            self.is_recording = False
            self.process = None
        except Exception as e:
            print(f"[REC Warning] Video recording failed to initialize ({e}). Recording skipped.")
            self.is_recording = False
            self.process = None

    async def stop(self):
        if not self.is_recording and not self.process:
            return

        self.is_recording = False

        if self.task:
            try:
                await self.task
            except Exception:
                pass
            self.task = None

        if self.process:
            try:
                # Properly close stdin so FFmpeg writes trailer
                if self.process.stdin:
                    self.process.stdin.flush()
                    self.process.stdin.close()

                # Wait for ffmpeg to finalize file
                return_code = self.process.wait(timeout=5)

                if return_code != 0:
                    stderr_output = self.process.stderr.read().decode() if self.process.stderr else ""
                    print("FFmpeg error on stop:", stderr_output)

            except Exception as e:
                print("FFmpeg shutdown warning:", e)
                try:
                    self.process.kill()
                except Exception:
                    pass
            finally:
                self.process = None

        print(f"[REC] Video recording stopped: {self.output_path}")

    async def record_loop(self):
        while self.is_recording:
            start_time = asyncio.get_event_loop().time()

            first_stream = self.first_stream.get_recent_frame() if self.first_stream else None
            second_stream = self.second_stream.get_recent_frame() if self.second_stream else None

            if first_stream is None:
                first_stream = np.zeros((480, 640, 3), dtype=np.uint8)
            else:
                first_stream = cv2.resize(first_stream, (640, 480))

            if second_stream is None:
                second_stream = np.zeros((480, 640, 3), dtype=np.uint8)
            else:
                second_stream = cv2.resize(second_stream, (640, 480))

            combined = np.hstack((first_stream, second_stream))

            canvas = np.zeros((self.total_height, self.total_width, 3), dtype=np.uint8)
            canvas[self.top_padding:self.top_padding + self.height, 0:self.width] = combined

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if self.inspection_type == "Box":
                header_text = f"Date: {timestamp} | Lot: {self.lot_number}"
            else:
                header_text = f"Date: {timestamp} | Lot: {self.lot_number} | Box: {self.box_number}"

            cv2.putText(
                canvas,
                header_text,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            try:
                self.process.stdin.write(canvas.tobytes())
            except Exception as e:
                print("FFmpeg write failed:", e)
                self.is_recording = False
                break

            elapsed = asyncio.get_event_loop().time() - start_time
            await asyncio.sleep(max(0, (1.0 / self.fps) - elapsed))