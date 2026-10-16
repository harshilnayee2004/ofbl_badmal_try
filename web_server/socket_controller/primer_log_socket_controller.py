import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

router = APIRouter()
primer_log_router = router
primer_log_manager = ConnectionManager()
fuze_log_manager = primer_log_manager

@router.websocket("/ws/primer_log/{primer_id}")
@router.websocket("/ws/fuze_log/{primer_id}")
async def primer_log_ws(ws: WebSocket, primer_id: int):
    room_name = f"primer_{primer_id}"
    await primer_log_manager.connect(ws, room_name)
    # Also support legacy room name
    legacy_room = f"fuze_{primer_id}"
    await primer_log_manager.connect(ws, legacy_room)
    logger.info(f"Primer Log Client Connected to log room: {room_name}")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        primer_log_manager.disconnect(ws, room_name)
        primer_log_manager.disconnect(ws, legacy_room)
        logger.info(f"Primer Log Client Disconnected from log room: {room_name}")

# Backward compatibility alias
fuze_log_ws = primer_log_ws
