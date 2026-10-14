import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

inspection_carrier_router = APIRouter()
inspection_carrier_manager = ConnectionManager()

@inspection_carrier_router.websocket("/ws/inspection_carrier")
async def inspection_carrier_ws(ws: WebSocket):
    await inspection_carrier_manager.connect(ws)
    logger.info("Carrier 6A/L Inspection Client Connected")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        inspection_carrier_manager.disconnect(ws)
        logger.info("Carrier 6A/L Inspection Client Disconnected")
