import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

carrier_log_router = APIRouter()
carrier_log_manager = ConnectionManager()

@carrier_log_router.websocket("/ws/carrier_log/{carrier_id}")
async def carrier_log_ws(ws: WebSocket, carrier_id: int):
    room_name = f"carrier_{carrier_id}"
    await carrier_log_manager.connect(ws, room_name=room_name)
    logger.info(f"Carrier Log Client Connected for Carrier {carrier_id}")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        carrier_log_manager.disconnect(ws, room_name=room_name)
        logger.info(f"Carrier Log Client Disconnected for Carrier {carrier_id}")
