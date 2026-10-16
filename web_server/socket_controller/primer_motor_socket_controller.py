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

primer_motor_router = APIRouter()
primer_motor_manager = ConnectionManager()

@primer_motor_router.websocket("/ws/primer_motor")
@primer_motor_router.websocket("/ws/fuze_motor")
async def primer_motor_ws(ws: WebSocket):
    await primer_motor_manager.connect(ws)
    CurrentInstanceRepositories.primer_box_turn_motor_status = True
    CurrentInstanceRepositories.fuze_motor_status = True
    logger.info("Primer 1A/L Motor Client Connected")

    try:
        while True:
            request = await ws.receive_json()
            command = request.get("command")
            if command == "status":
                angle = request.get("angle")
                FuzeInspectionRepository.motor_angle = angle
            elif command == "rotate_fuze" or command == "rotate_primer":
                angle = request.get("angle")
                await primer_motor_manager.send_json({"command": "rotate_primer", "angle": angle})
    except WebSocketDisconnect:
        primer_motor_manager.disconnect(ws)
        CurrentInstanceRepositories.primer_box_turn_motor_status = False
        CurrentInstanceRepositories.fuze_motor_status = False
        logger.info("Primer 1A/L Motor Client Disconnected")

# Aliases for backward compatibility
fuze_motor_router = primer_motor_router
fuze_motor_manager = primer_motor_manager
fuze_motor_ws = primer_motor_ws
