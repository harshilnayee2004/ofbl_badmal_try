import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


router = APIRouter()
fuze_log_manager = ConnectionManager()

@router.websocket("/ws/fuze_log/{fuze_id}")
async def fuze_log_ws(ws: WebSocket, fuze_id: int):
    room_name = f"fuze_{fuze_id}"
    await fuze_log_manager.connect(ws, room_name)
    logger.info(f"Fuze Log Client Connected to fuze log room: {room_name}")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        fuze_log_manager.disconnect(ws, room_name)
        logger.info(f"Fuze Log Client Disconnected from fuze log room: {room_name}")
