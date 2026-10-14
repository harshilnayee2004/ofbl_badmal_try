import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

inspection_fuze_router = APIRouter()
inspection_fuze_manager = ConnectionManager()

@inspection_fuze_router.websocket("/ws/inspection_fuze")
@inspection_fuze_router.websocket("/ws/inspection_primer")
async def inspection_fuze_ws(ws: WebSocket):
    await inspection_fuze_manager.connect(ws)
    logger.info("Primer / Fuze Inspection Client Connected")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        inspection_fuze_manager.disconnect(ws)
        logger.info("Primer / Fuze Inspection Client Disconnected")