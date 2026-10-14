import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager
from repositories.current_inspection_repositories import BoxInspectionRepository
from repositories.current_instance_repositories import CurrentInstanceRepositories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


box_motor_router = APIRouter()
box_motor_manager = ConnectionManager()

@box_motor_router.websocket("/ws/primer_box_motor")
@box_motor_router.websocket("/ws/box_motor")
async def box_motor_ws(ws: WebSocket):
    await box_motor_manager.connect(ws)
    CurrentInstanceRepositories.primer_box_turn_motor_status = True
    CurrentInstanceRepositories.box_motor_status = True
    logger.info("Primer/Box Motor Client Connected")

    try:
        while True:
            # optional: receive ping / commands from frontend
            request = await ws.receive_json()
            print(request)
            if request.get("type") == "info":
                command = request.get("object")
                BoxInspectionRepository.motor_angle = command.get("angle")
    except WebSocketDisconnect:
        box_motor_manager.disconnect(ws)
        if len(box_motor_manager.active_connections) == 0:
            CurrentInstanceRepositories.primer_box_turn_motor_status = False
            CurrentInstanceRepositories.box_motor_status = False
        logger.info("Primer/Box Motor Client Disconnected")