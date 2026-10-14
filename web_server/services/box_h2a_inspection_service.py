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
from models.box_model import Box
from models.box_h2a_inspection_model import BoxH2AInspection
from services.log_service import BoxLogService
from services.video_recording_service import VideoRecorder
from services.box_h2a_sequence_service import BoxH2ASequenceService
from repositories.camera_repositories import CameraRepository
from repositories.current_inspection_repositories import BoxH2AInspectionRepository
from repositories.inspection_sequence_repositories import BoxH2AInspectionDetails
from socket_controller.box_motor_socket_controller import box_motor_manager
from socket_controller.box_inspection_socket_controller import inspection_box_manager
from socket_controller.lot_inspection_socket_controller import inspection_lot_manager

class BoxH2AInspectionService:
    """
    Inspection Service for Level 2 Packaging: Box H2A
    Controls 12-sequence inspection pipeline:
      - Motor rotation & positioning
      - Operator unpack & countdown prompts
      - Video recording & frame extraction
      - AI Server inference via /inspect_box/h2a
      - Log entries & WebSocket broadcasts
    """

    @staticmethod
    async def start_inspection(box_id: int, lot_number: str, suppress_cam_error: bool = None):
        with Session(engine) as db:
            box_log_service = BoxLogService(db)
            box_obj = db.exec(select(Box).where(Box.id == box_id)).first()
            if not box_obj:
                return

            BoxH2AInspectionRepository.current_box_id = box_id
            BoxH2AInspectionRepository.current_box_sequence = box_obj.sequence_number or 1
            BoxH2AInspectionRepository.inspection_command = "Continue"

            first_stream = CameraRepository.stream_dict.get("PRIMER_BOX_TOP")
            second_stream = CameraRepository.stream_dict.get("PRIMER_BOX_TURN_SIDE")

            recorder = VideoRecorder(
                output_dir=box_obj.files_path,
                lot_number=lot_number,
                inspection_type="Box_H2A",
                first_stream=first_stream,
                second_stream=second_stream
            )

            try:
                await recorder.start()
                await inspection_box_manager.send_json({
                    "type": "recording_status",
                    "object": {"status": True}
                })
                BoxH2AInspectionRepository.recording_status = True

                sequence_list = BoxH2AInspectionDetails.sequences

                for sequence in sequence_list:
                    camera_position = sequence.get("camera_position")
                    sequence_number = sequence.get("sequence_number")
                    wait_time = sequence.get("wait_time", 0)
                    instruction = sequence.get("instruction", "")
                    motor_angle = sequence.get("motor_angle", 0)

                    # Update current step
                    BoxH2AInspectionRepository.current_step = sequence_number

                    # Motor rotation
                    if BoxH2AInspectionRepository.motor_angle != motor_angle:
                        await box_motor_manager.send_json({"type": "command", "object": {"angle": motor_angle}})
                        await box_log_service.add_box_log(
                            description=f"Turntable: Rotating to {motor_angle}° for Sequence #{sequence_number}",
                            box_id=box_id
                        )

                    while True:
                        if BoxH2AInspectionRepository.motor_angle == motor_angle:
                            BoxH2AInspectionRepository.motor_angle = 0
                            break
                        if BoxH2AInspectionRepository.inspection_command == "Stopped":
                            await recorder.stop()
                            await inspection_box_manager.send_json({
                                "type": "recording_status",
                                "object": {"status": False}
                            })
                            await box_log_service.add_box_log(description="Inspection Stopped By Operator", box_id=box_id)
                            return
                        await asyncio.sleep(1)

                    await inspection_box_manager.send_json({
                        "type": "instruction",
                        "object": {"text": instruction, "wait_time": wait_time}
                    })

                    BoxH2AInspectionRepository.current_inspection_instruction = instruction
                    BoxH2AInspectionRepository.current_wait_time = wait_time
                    BoxH2AInspectionRepository.timer_start_time = datetime.now()

                    await box_log_service.add_box_log(
                        description=f"Starting Box H2A Sequence #{sequence_number}: {instruction}",
                        box_id=box_id
                    )

                    await inspection_box_manager.send_json({
                        "type": "camera_position",
                        "object": {"position": camera_position}
                    })

                    if wait_time > 0:
                        await box_log_service.add_box_log(
                            description=f"Waiting For Operator Unpacking / Prep ({wait_time}s)...",
                            box_id=box_id
                        )
                        await asyncio.sleep(wait_time)

                    # Check for Pause/Stop
                    while True:
                        if BoxH2AInspectionRepository.inspection_command == "Stopped":
                            await recorder.stop()
                            await inspection_box_manager.send_json({
                                "type": "recording_status",
                                "object": {"status": False}
                            })
                            await box_log_service.add_box_log(description="Inspection Stopped By Operator", box_id=box_id)
                            return
                        if BoxH2AInspectionRepository.inspection_command == "Paused":
                            await asyncio.sleep(1)
                            continue
                        break

                    await asyncio.sleep(1)

                    is_suppressed = settings.IS_DEV and (suppress_cam_error if suppress_cam_error is not None else getattr(CameraRepository, 'suppress_camera_error', False))

                    # Frame capture
                    stream = CameraRepository.stream_dict.get(camera_position) or first_stream
                    if stream:
                        frame = stream.get_recent_frame()
                    else:
                        frame = None

                    if frame is None:
                        if not is_suppressed:
                            raise Exception(f"Camera stream not found or offline for position: {camera_position}")

                        await box_log_service.add_box_log(
                            description=f"[DEV] Missing frame from {camera_position} - using mock data (Suppressed)",
                            box_id=box_id
                        )
                        mock_result = {
                            f"SIDE_{sequence_number}_STENCILING": True,
                            "EXPLOSIVE_LABEL": True,
                            "WOODEN_SHEET": True,
                            "PACKING_SLIP": True,
                            "COTTON_SHEET": True,
                            "PRIMER_QUANTITY_COUNT": True,
                            "COUNT": 36,
                            "WOODEN_SHEET_18_HOLES": True,
                            "INTERIOR_RUST_PEELING_PAINT": False
                        }
                        await BoxH2ASequenceService.process_result(db, sequence_number, box_id, mock_result, box_log_service)
                    else:
                        success, buffer = cv2.imencode(".jpg", frame)
                        if not success:
                            if not is_suppressed:
                                raise Exception(f"Failed to encode frame from {camera_position}")
                            buffer = np.zeros((100,), dtype=np.uint8)

                        image_bytes = buffer.tobytes()
                        image_filename = f"box_h2a_sequence_{sequence_number}.jpeg"
                        image_path = os.path.join(box_obj.files_path, image_filename)
                        with open(image_path, "wb") as f:
                            f.write(image_bytes)

                        await box_log_service.add_box_log(
                            description=f"Captured Frame From {camera_position}",
                            box_id=box_id
                        )

                        try:
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                files = {"image": ("frame.jpg", image_bytes, "image/jpeg")}
                                data = {
                                    "box_id": box_id,
                                    "sequence_number": sequence_number,
                                    "lot_number": lot_number
                                }
                                response = await client.post(
                                    f"{settings.AI_SERVER_URL}inspect_box/h2a",
                                    data=data,
                                    files=files
                                )
                                if response.status_code == 200:
                                    result = response.json()
                                    result_dict = json.loads(result.get("object", "{}")) if isinstance(result.get("object"), str) else result.get("object", {})
                                    await BoxH2ASequenceService.process_result(db, sequence_number, box_id, result_dict, box_log_service)
                                else:
                                    raise Exception(f"AI Server returned status code {response.status_code}")
                        except Exception as ai_err:
                            if not is_suppressed:
                                raise Exception(f"AI Analysis failed for sequence #{sequence_number}: {ai_err}")
                            print(f"Box H2A AI Server Error (Suppressed): {ai_err}")
                            mock_result = {
                                f"SIDE_{sequence_number}_STENCILING": True,
                                "EXPLOSIVE_LABEL": True,
                                "WOODEN_SHEET": True,
                                "PACKING_SLIP": True,
                                "COTTON_SHEET": True,
                                "PRIMER_QUANTITY_COUNT": True,
                                "COUNT": 36,
                                "WOODEN_SHEET_18_HOLES": True,
                                "INTERIOR_RUST_PEELING_PAINT": False
                            }
                            await BoxH2ASequenceService.process_result(db, sequence_number, box_id, mock_result, box_log_service)

                    await box_log_service.add_box_log(
                        description=f"Completed Box H2A Sequence #{sequence_number}",
                        box_id=box_id
                    )

                # Finalize Box Inspection
                await recorder.stop()
                await inspection_box_manager.send_json({
                    "type": "recording_status",
                    "object": {"status": False}
                })
                BoxH2AInspectionRepository.recording_status = False

                box_obj.end_time = datetime.now()
                box_obj.box_inspection_status = "Completed"
                db.add(box_obj)
                db.commit()

                await inspection_box_manager.send_json({
                    "type": "box_update",
                    "object": {
                        "box_id": box_obj.id,
                        "sequence_number": box_obj.sequence_number,
                        "box_inspection_status": box_obj.box_inspection_status,
                        "acceptance_status": box_obj.acceptance_status
                    }
                })

                await inspection_lot_manager.send_json({
                    "type": "lot_update",
                    "object": {"lot_number": lot_number, "action": "box_completed", "box_id": box_id}
                })

            except Exception as e:
                print(f"Box H2A Inspection Error: {e}")
                await recorder.stop()
                BoxH2AInspectionRepository.recording_status = False
                box_obj.box_inspection_status = "Failed"
                db.add(box_obj)
                db.commit()
                await box_log_service.add_box_log(
                    description=f"Inspection Error: {str(e)}",
                    box_id=box_id
                )
                await inspection_box_manager.send_json({
                    "type": "box_update",
                    "object": {
                        "box_id": box_obj.id,
                        "sequence_number": box_obj.sequence_number,
                        "inspection_status": "Failed",
                        "description": f"Inspection Error: {str(e)}"
                    }
                })
                await inspection_box_manager.send_json({
                    "type": "instruction",
                    "object": {"text": "Inspection Failed To Continue Please Check The Camera Connections", "wait_time": 0}
                })
