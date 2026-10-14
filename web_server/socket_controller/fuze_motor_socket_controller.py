import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from repositories.current_inspection_repositories import FuzeInspectionRepository
from repositories.current_instance_repositories import CurrentInstanceRepositories
from socket_controller.socket_manager import ConnectionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


fuze_motor_router = APIRouter()
fuze_motor_manager = ConnectionManager()

@fuze_motor_router.websocket("/ws/fuze_motor")
@fuze_motor_router.websocket("/ws/primer_motor")
async def fuze_motor_ws(ws: WebSocket):
    await fuze_motor_manager.connect(ws)
    CurrentInstanceRepositories.primer_box_turn_motor_status = True
    CurrentInstanceRepositories.fuze_motor_status = True
    logger.info("Primer/Fuze Motor Client Connected")

    try:
        while True:
            # optional: receive ping / commands from frontend
            request = await ws.receive_json()
            print(request)
            if request.get("type") == "info":
                command = request.get("object")
                FuzeInspectionRepository.motor_angle = command.get("angle")
    except WebSocketDisconnect:
        fuze_motor_manager.disconnect(ws)
        if len(fuze_motor_manager.active_connections) == 0:
            CurrentInstanceRepositories.primer_box_turn_motor_status = False
            CurrentInstanceRepositories.fuze_motor_status = False
        logger.info("Primer/Fuze Motor Client Disconnected")