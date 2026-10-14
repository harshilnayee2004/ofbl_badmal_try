from fastapi import APIRouter
from schemas.response_dto import ResponseDTO
from socket_controller.box_motor_socket_controller import box_motor_manager
from socket_controller.fuze_motor_socket_controller import fuze_motor_manager
from socket_controller.carrier_motor_socket_controller import carrier_motor_manager


router = APIRouter(
    prefix="/motor",
    tags=["Motor"]
)


@router.get("/carrier/{angle}")
@router.get("/cerrier/{angle}")
async def carrier_motor(angle: int):
    await carrier_motor_manager.send_json({"type": "command", "object": {"angle": angle}})
    return ResponseDTO(
        status=True,
        message=f"Carrier motor rotated {angle} degrees",
        object=None
    )


@router.get("/primer_box/{angle}")
@router.get("/box/{angle}")
async def box_motor(angle: int):
    await box_motor_manager.send_json({"type": "command", "object": {"angle": angle}})
    return ResponseDTO(
        status=True,
        message=f"Primer/Box motor rotated {angle} degrees",
        object=None
    )


@router.get("/fuze/{angle}")
async def fuze_motor(angle: int):
    await fuze_motor_manager.send_json({"type": "command", "object": {"angle": angle}})
    # Also forward to box_motor_manager if needed
    if len(box_motor_manager.active_connections) > 0 and len(fuze_motor_manager.active_connections) == 0:
        await box_motor_manager.send_json({"type": "command", "object": {"angle": angle}})
    return ResponseDTO(
        status=True,
        message=f"Primer/Box motor rotated {angle} degrees",
        object=None
    )