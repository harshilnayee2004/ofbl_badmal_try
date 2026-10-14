import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


router = APIRouter()
box_log_manager = ConnectionManager()

@router.websocket("/ws/box_log/{box_id}")
async def box_log_ws(ws: WebSocket, box_id: int):
    room_name = f"box_{box_id}"
    await box_log_manager.connect(ws, room_name)
    logger.info(f"Box Log Client Connected to box log room: {room_name}")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        box_log_manager.disconnect(ws, room_name)
        logger.info(f"Box Log Client Disconnected from box log room: {room_name}")
