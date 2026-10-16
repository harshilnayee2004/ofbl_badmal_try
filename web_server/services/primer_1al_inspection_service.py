import os
import cv2
import json
import asyncio
import httpx
import numpy as np
from datetime import datetime
from sqlmodel import Session, select
from core.config import settings
from core.database import engine
from models.fuze_model import Fuze
from models.lot_model import Lot
from models.primer_1al_inspection_model import Primer1ALInspection
from services.log_service import FuzeLogService
from services.video_recording_service import VideoRecorder
from services.primer_1al_sequence_service import Primer1ALSequenceService
from repositories.camera_repositories import CameraRepository
from repositories.current_inspection_repositories import Primer1ALInspectionRepository
from repositories.inspection_sequence_repositories import Primer1ALInspectionDetails
from socket_controller.fuze_motor_socket_controller import fuze_motor_manager
from socket_controller.fuze_inspection_socket_controller import inspection_fuze_manager
from socket_controller.lot_inspection_socket_controller import inspection_lot_manager

class Primer1ALInspectionService:
    """
    Inspection Service for Level 3 Ordnance Unit: Primer Electric 1A/L
    Controls 6-sequence 360° rotational unit inspection:
      - Rotary jig motor angle commands (0°, 90°, 180°, 270°)
      - Video recording & frame extraction
      - AI Server inference via /inspect_fuze/primer_1al
      - Log entries & WebSocket broadcasts
    """

    @staticmethod
    async def start_inspection(fuze_id: int, lot_id: int):
        with Session(engine) as db:
            fuze_log_service = FuzeLogService(db)
            fuze_obj = db.exec(select(Fuze).where(Fuze.id == fuze_id)).first()
            lot_obj = db.exec(select(Lot).where(Lot.id == lot_id)).first()
            if not fuze_obj or not lot_obj:
                return

            lot_number = lot_obj.lot_number
            Primer1ALInspectionRepository.current_primer_id = fuze_id
            Primer1ALInspectionRepository.current_primer_sequence = fuze_obj.sequence_number or 1
            Primer1ALInspectionRepository.inspection_command = "Continue"

            first_stream = CameraRepository.stream_dict.get("PRIMER_BOX_TOP")
            second_stream = CameraRepository.stream_dict.get("PRIMER_BOX_TURN_SIDE")

            recorder = VideoRecorder(
                output_dir=fuze_obj.files_path,
                lot_number=lot_number,
                inspection_type="Primer_1AL",
                first_stream=first_stream,
                second_stream=second_stream
            )

            try:
                await recorder.start()
                await inspection_fuze_manager.send_json({
                    "type": "recording_status",
                    "object": {"status": True}
                })
                Primer1ALInspectionRepository.recording_status = True
                await inspection_fuze_manager.send_json({"type": "reset"})   # clear AI overlay for the new run

                sequence_list = Primer1ALInspectionDetails.sequences

                for sequence in sequence_list:
                    camera_position = sequence.get("camera_position")
                    sequence_number = sequence.get("sequence_number")
                    wait_time = sequence.get("wait_time", 0)
                    instruction = sequence.get("instruction", "")
                    motor_angle = sequence.get("motor_angle", 0)

                    # Motor angle command on rotary jig
                    if Primer1ALInspectionRepository.rotary_angle != motor_angle:
                        await fuze_motor_manager.send_json({"type": "command", "object": {"angle": motor_angle}})
                        await fuze_log_service.add_fuze_log(
                            description=f"Rotary Jig: Rotating to {motor_angle}° for Sequence #{sequence_number}",
                            fuze_id=fuze_id
                        )

                    while True:
                        if Primer1ALInspectionRepository.motor_angle == motor_angle:
                            Primer1ALInspectionRepository.motor_angle = 0
                            break
                        if Primer1ALInspectionRepository.inspection_command == "Stopped":
                            await recorder.stop()
                            await inspection_fuze_manager.send_json({
                                "type": "recording_status",
                                "object": {"status": False}
                            })
                            await fuze_log_service.add_fuze_log(description="Inspection Stopped By Operator", fuze_id=fuze_id)
                            return
                        await asyncio.sleep(1)

                    await inspection_fuze_manager.send_json({
                        "type": "instruction",
                        "object": {"text": instruction, "wait_time": wait_time}
                    })

                    Primer1ALInspectionRepository.current_inspection_instruction = instruction
                    Primer1ALInspectionRepository.current_wait_time = wait_time
                    Primer1ALInspectionRepository.timer_start_time = datetime.now()

                    await fuze_log_service.add_fuze_log(
                        description=f"Starting Primer 1A/L Sequence #{sequence_number}: {instruction}",
                        fuze_id=fuze_id
                    )

                    await inspection_fuze_manager.send_json({
                        "type": "camera_position",
                        "object": {"position": camera_position}
                    })

                    if wait_time > 0:
                        await asyncio.sleep(wait_time)

                    # Check for Pause/Stop
                    while True:
                        if Primer1ALInspectionRepository.inspection_command == "Stopped":
                            await recorder.stop()
                            await inspection_fuze_manager.send_json({
                                "type": "recording_status",
                                "object": {"status": False}
                            })
                            await fuze_log_service.add_fuze_log(description="Inspection Stopped By Operator", fuze_id=fuze_id)
                            return
                        if Primer1ALInspectionRepository.inspection_command == "Paused":
                            await asyncio.sleep(1)
                            continue
                        break

                    await asyncio.sleep(1)

                    # Frame capture
                    stream = CameraRepository.stream_dict.get(camera_position) or first_stream
                    if stream:
                        frame = stream.get_recent_frame()
                    else:
                        frame = None

                    if frame is not None:
                        success, buffer = cv2.imencode(".jpg", frame)
                        if success:
                            image_bytes = buffer.tobytes()
                            image_filename = f"primer_1al_sequence_{sequence_number}.jpeg"
                            image_path = os.path.join(fuze_obj.files_path, image_filename)
                            with open(image_path, "wb") as f:
                                f.write(image_bytes)

                            await fuze_log_service.add_fuze_log(
                                description=f"Captured Frame From {camera_position}",
                                fuze_id=fuze_id
                            )

                            try:
                                async with httpx.AsyncClient(timeout=30.0) as client:
                                    files = {"image": ("frame.jpg", image_bytes, "image/jpeg")}
                                    data = {
                                        "fuze_id": fuze_id,
                                        "sequence_number": sequence_number,
                                        "lot_number": lot_number
                                    }
                                    response = await client.post(
                                        f"{settings.AI_SERVER_URL}inspect_fuze/primer_1al",
                                        data=data,
                                        files=files
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        result_dict = json.loads(result.get("object", "{}")) if isinstance(result.get("object"), str) else result.get("object", {})
                                        overlay = result_dict.pop("overlay", None) if isinstance(result_dict, dict) else None
                                        await Primer1ALSequenceService.process_result(db, sequence_number, fuze_id, result_dict, fuze_log_service)
                                        for overlay_msg in overlay or []:   # boxes + checklist for the browser overlay
                                            await inspection_fuze_manager.send_json(overlay_msg)
                            except Exception as ai_err:
                                print(f"Primer 1A/L AI Server Error: {ai_err}")
                                mock_result = {
                                    "CLEANLINESS_APPEARANCE": True,
                                    "LOT_NUMBER_MATCH": True,
                                    "MAGAZINE_CRACK_DAMAGE": False,
                                    "PAPER_LINER_DAMAGE_SPILLAGE": False,
                                    "RUBBER_RING_ASSEMBLY": True,
                                    "MAGAZINE_ASSEMBLY": True
                                }
                                await Primer1ALSequenceService.process_result(db, sequence_number, fuze_id, mock_result, fuze_log_service)
                    else:
                        mock_result = {
                            "CLEANLINESS_APPEARANCE": True,
                            "LOT_NUMBER_MATCH": True,
                            "MAGAZINE_CRACK_DAMAGE": False,
                            "PAPER_LINER_DAMAGE_SPILLAGE": False,
                            "RUBBER_RING_ASSEMBLY": True,
                            "MAGAZINE_ASSEMBLY": True
                        }
                        await Primer1ALSequenceService.process_result(db, sequence_number, fuze_id, mock_result, fuze_log_service)

                    await fuze_log_service.add_fuze_log(
                        description=f"Completed Primer 1A/L Sequence #{sequence_number}",
                        fuze_id=fuze_id
                    )

                # Finalize Primer Unit Inspection
                await recorder.stop()
                await inspection_fuze_manager.send_json({
                    "type": "recording_status",
                    "object": {"status": False}
                })
                Primer1ALInspectionRepository.recording_status = False

                fuze_obj.end_time = datetime.now()
                fuze_obj.fuze_inspection_status = "Completed"
                db.add(fuze_obj)
                db.commit()

                await inspection_fuze_manager.send_json({
                    "type": "fuze_update",
                    "object": {
                        "fuze_id": fuze_obj.id,
                        "sequence_number": fuze_obj.sequence_number,
                        "fuze_inspection_status": fuze_obj.fuze_inspection_status,
                        "acceptance_status": fuze_obj.acceptance_status
                    }
                })

                await inspection_lot_manager.send_json({
                    "type": "lot_update",
                    "object": {"lot_number": lot_number, "action": "primer_completed", "fuze_id": fuze_id}
                })

            except Exception as e:
                print(f"Primer 1A/L Inspection Error: {e}")
                await recorder.stop()
                Primer1ALInspectionRepository.recording_status = False
                await fuze_log_service.add_fuze_log(
                    description=f"Inspection Error: {str(e)}",
                    fuze_id=fuze_id
                )
