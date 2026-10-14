import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


inspection_lot_router = APIRouter()
inspection_lot_manager = ConnectionManager()

@inspection_lot_router.websocket("/ws/inspection_lot")
async def inspection_lot_ws(ws: WebSocket):
    await inspection_lot_manager.connect(ws)
    logger.info("Lot Inspection Client Connected")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        inspection_lot_manager.disconnect(ws)
        logger.info("Lot Inspection Client Disconnected")