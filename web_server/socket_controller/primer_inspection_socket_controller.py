import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

inspection_primer_router = APIRouter()
inspection_primer_manager = ConnectionManager()

@inspection_primer_router.websocket("/ws/inspection_primer")
@inspection_primer_router.websocket("/ws/inspection_fuze")
async def inspection_primer_ws(ws: WebSocket):
    await inspection_primer_manager.connect(ws)
    logger.info("Primer 1A/L Inspection Client Connected")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        inspection_primer_manager.disconnect(ws)
        logger.info("Primer 1A/L Inspection Client Disconnected")

# Aliases for backward compatibility
inspection_fuze_router = inspection_primer_router
inspection_fuze_manager = inspection_primer_manager
inspection_fuze_ws = inspection_primer_ws
