import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


admin_dashboard_router = APIRouter()
admin_dashboard_manager = ConnectionManager()

@admin_dashboard_router.websocket("/ws/admin_dashboard")
async def admin_dashboard_ws(ws: WebSocket):
    await admin_dashboard_manager.connect(ws)
    logger.info("Admin Dashboard Client Connected")

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        admin_dashboard_manager.disconnect(ws)
        logger.info("Admin Dashboard Client Disconnected")