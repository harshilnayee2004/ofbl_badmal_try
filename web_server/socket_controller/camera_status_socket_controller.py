import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


camera_status_router = APIRouter()
camera_status_manager = ConnectionManager()

@camera_status_router.websocket("/ws/camera_status")
async def camera_status_ws(ws: WebSocket):
    await camera_status_manager.connect(ws)
    logger.info("Camera Status Client Connected")

    try:
        while True:
            # optional: receive ping / commands from frontend
            await ws.receive_text()
    except WebSocketDisconnect:
        camera_status_manager.disconnect(ws)
        logger.info("Camera Status Client Disconnected")