from core.config import settings
import cv2
import time
import numpy as np
from typing import List
from sqlmodel import Session, select
from models.camera_model import Camera
from schemas.camera_dto import CameraUpdate
from services.stream_manager import StreamManager
from services.stream_service import StreamingService
from repositories.camera_repositories import CameraRepository

class CameraService:
    @staticmethod
    def get_all_cameras(db: Session) -> List[Camera]:
        camera_list=db.exec(select(Camera)).all()
        cameras=[]
        for camera in camera_list:
            camera_obj={}
            streaming_service_obj=CameraRepository.stream_dict[camera.position]
            camera_obj["status"]="offline"
            if streaming_service_obj is not None:
                camera_obj["status"]=streaming_service_obj.online_status
            camera_obj["id"]=camera.id
            camera_obj["ip_address"]=camera.ip_address
            camera_obj["port"]=camera.port
            camera_obj["username"]=camera.username
            camera_obj["password"]=camera.password
            camera_obj["rtsp_url"]=camera.rtsp_url
            camera_obj["position"]=camera.position
            cameras.append(camera_obj)
        return cameras

    @staticmethod
    def get_camera_by_id(db: Session, camera_id: int) -> Camera:
        return db.exec(select(Camera).where(Camera.id == camera_id)).first()

    @staticmethod
    async def update_camera(db: Session, camera_id: int, camera_data: CameraUpdate) -> dict[
                                                                                     str,str] | None:
        camera = db.exec(select(Camera).where(Camera.id == camera_id)).first()
        if not camera:
            return None
        
        camera.ip_address = camera_data.ip_address
        camera.port = camera_data.port
        camera.username = camera_data.username
        camera.password = camera_data.password
        if "COUNT_WALL" in camera.position  :
            camera.rtsp_url = "rtsp://"+camera.username+":"+camera.password+"@"+camera.ip_address + ":" + str(camera.port) + "/ch01.264"
        else:
            camera.rtsp_url = "rtsp://"+camera.username+":"+camera.password+"@"+camera.ip_address + ":" + str(camera.port) + "/stream1"

        # CameraRepository.stream_dict[camera.position] = StreamingService(
        #     camera_id=camera.id,
        #     position=camera.position,
        #     rtsp_url="rtsp://"+camera.username+":"+camera.password+"@"+camera.ip_address + ":" + str(camera.port) + "/stream0",
        # )
        stream_service=CameraRepository.stream_dict[camera.position]
        if stream_service is not None:
            stream_service.stop()
        stream_service=StreamingService(
            camera_id=camera.id,
            position=camera.position,
            rtsp_url=camera.rtsp_url,
        )
        CameraRepository.stream_dict[camera.position] = stream_service
        StreamManager.restart_stream(camera.position)
        
        db.commit()
        db.refresh(camera)
        return {
            "ip_address":camera.ip_address,
            "port":camera.port,
            "username":camera.username,
            "password":camera.password
        }
    
    @staticmethod
    def mjpeg_frame_generator(streaming_service, position):
        """
        HTTP MJPEG frame generator
        """
        boundary = b"--frame"
        zones = {}

        if position == "WATER_TANK_TOP":

            # TOP ROW
            TOP_X, TOP_Y, TOP_W, TOP_H, TOP_GAP = 375, 2, 650, 850, 0

            # BOTTOM ROW
            BOT_X, BOT_Y, BOT_W, BOT_H, BOT_GAP = 375, 850, 650, 800, 0

            for i in range(5):
                x = TOP_X + i * (TOP_W + TOP_GAP)
                zones[f"Z{i+1}"] = (x, TOP_Y, TOP_W, TOP_H)

            for i in range(5):
                x = BOT_X + i * (BOT_W + BOT_GAP)
                zones[f"Z{i+6}"] = (x, BOT_Y, BOT_W, BOT_H)

        while True:
            if streaming_service is None:
                # Load placeholder image
                placeholder_path = settings.NO_FEED_IMAGE_PATH
                frame = cv2.imread(placeholder_path)
                if frame is None:
                    # Fallback to black frame if placeholder missing
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                
                
                # Encode placeholder
                success, jpeg = cv2.imencode(".jpg", frame)
                if success:
                    yield (
                            boundary + b"\r\n"
                                       b"Content-Type: image/jpeg\r\n"
                                       b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" +
                            jpeg.tobytes() + b"\r\n"
                    )
                time.sleep(0.5) # Lower frequency for static placeholder
                continue

            frame = None
            if streaming_service.running and streaming_service.connected:
                frame = streaming_service.get_recent_frame()

            if frame is None:
                # Load placeholder image
                placeholder_path = settings.NO_FEED_IMAGE_PATH
                frame = cv2.imread(placeholder_path)
                if frame is None:
                    # Fallback to black frame if placeholder missing
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                
                
                # Encode placeholder
                success, jpeg = cv2.imencode(".jpg", frame)
                if success:
                    yield (
                            boundary + b"\r\n"
                                       b"Content-Type: image/jpeg\r\n"
                                       b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" +
                            jpeg.tobytes() + b"\r\n"
                    )
                time.sleep(0.5) # Lower frequency for static placeholder
                continue

            if position == "WATER_TANK_TOP":
                for name, (x, y, w, h) in zones.items():
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 220, 0), 2)
                    cv2.putText(
                        frame,
                        name,
                        (x + 4, y + 18),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 255, 0),
                        2
                    )
                    # frame = cv2.resize(frame, (1280, 720))
            # Encode frame as JPEG
            success, jpeg = cv2.imencode(".jpg", frame, [
                cv2.IMWRITE_JPEG_QUALITY, 80
            ])

            if not success:
                continue

            yield (
                    boundary + b"\r\n"
                               b"Content-Type: image/jpeg\r\n"
                               b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" +
                    jpeg.tobytes() + b"\r\n"
            )

            # Control FPS (non-busy wait)
            time.sleep(1 / streaming_service.streaming_fps)