import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager
from repositories.current_inspection_repositories import CarrierInspectionRepository
from repositories.current_instance_repositories import CurrentInstanceRepositories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

carrier_motor_router = APIRouter()
carrier_motor_manager = ConnectionManager()

@carrier_motor_router.websocket("/ws/carrier_motor")
@carrier_motor_router.websocket("/ws/cerrier_motor")
async def carrier_motor_ws(ws: WebSocket):
    await carrier_motor_manager.connect(ws)
    CurrentInstanceRepositories.carrier_turn_motor_status = True
    CurrentInstanceRepositories.cerrier_turn_motor_status = True
    CurrentInstanceRepositories.carrier_motor_status = True
    logger.info("Carrier Motor Client Connected")

    try:
        while True:
            request = await ws.receive_json()
            if request.get("type") == "info":
                command = request.get("object", {})
                CarrierInspectionRepository.motor_angle = command.get("angle", 0)
    except WebSocketDisconnect:
        carrier_motor_manager.disconnect(ws)
        if len(carrier_motor_manager.active_connections) == 0:
            CurrentInstanceRepositories.carrier_turn_motor_status = False
            CurrentInstanceRepositories.cerrier_turn_motor_status = False
            CurrentInstanceRepositories.carrier_motor_status = False
        logger.info("Carrier Motor Client Disconnected")

