import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

inspection_box_router = APIRouter()
inspection_box_manager = ConnectionManager()

@inspection_box_router.websocket("/ws/inspection_box")
@inspection_box_router.websocket("/ws/inspection_h2a_box")
async def inspection_box_ws(ws: WebSocket):
    await inspection_box_manager.connect(ws)
    logger.info("Box / H2A Inspection Client Connected")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        inspection_box_manager.disconnect(ws)
        logger.info("Box / H2A Inspection Client Disconnected")