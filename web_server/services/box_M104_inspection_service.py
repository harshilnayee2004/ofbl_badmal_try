import os
import cv2
import json
import asyncio
import numpy as np
from datetime import datetime
from core.database import engine
from models.box_model import Box
from core.config import settings
from sqlmodel import Session, select
from sentry_sdk.integrations import httpx
from services.log_service import BoxLogService
from services.video_recording_service import VideoRecorder
from repositories.camera_repositories import CameraRepository
from models.box_M104_inspection_model import BoxM104Inspection
from services.box_M104_sequence_service import BoxM104SequenceService
from socket_controller.box_motor_socket_controller import box_motor_manager
from repositories.inspection_sequence_repositories import  M104InspectionDetails
from socket_controller.box_inspection_socket_controller import inspection_box_manager

class BoxM104InspectionService:

    @staticmethod
    async def start_inspection(box_id: int, lot_number: str, suppress_cam_error: bool = None):
        with Session(engine) as db:
            box_log_service = BoxLogService(db)
            box_obj = db.exec(select(Box).where(Box.id == box_id)).first()
            if not box_obj:
                return
            first_stream = CameraRepository.stream_dict.get("PRIMER_BOX_TOP")
            second_stream = CameraRepository.stream_dict.get("PRIMER_BOX_TURN_SIDE")
            recorder = VideoRecorder(output_dir=box_obj.files_path, lot_number=lot_number, inspection_type="Box",first_stream=first_stream,second_stream=second_stream)

            try:
                await recorder.start()
                await inspection_box_manager.send_json({
                    "type": "recording_status",
                    "object": {"status": True}
                })
                from repositories.current_inspection_repositories import BoxInspectionRepository
                BoxInspectionRepository.recording_status = True
                sequence_list = M104InspectionDetails.sequences

                for sequence in sequence_list:
                    camera_position = sequence.get("camera_position")
                    sequence_number = sequence.get('sequence_number')
                    wait_time = sequence.get('wait_time')
                    instruction = sequence.get('instruction', '')
                    motor_angle = sequence.get('motor_angle')
                    if motor_angle != 0:
                        if BoxInspectionRepository.motor_angle != motor_angle:
                            await box_motor_manager.send_json({"type": "command", "object": {"angle": motor_angle}})
                            await box_log_service.add_box_log(
                                description=f"Waiting For Motor To Turn {motor_angle} degree",
                                box_id=box_id)

                    while True:
                        if BoxInspectionRepository.motor_angle == motor_angle or motor_angle == 0:
                            BoxInspectionRepository.motor_angle = 0
                            break
                        if BoxInspectionRepository.inspection_command == "Stopped":
                            await recorder.stop()
                            await inspection_box_manager.send_json({
                                "type": "recording_status",
                                "object": {"status": False}
                            })
                            await box_log_service.add_box_log(description="Inspection Stopped By User", box_id=box_id)
                            return
                        await asyncio.sleep(1)

                    await inspection_box_manager.send_json({
                        "type": "instruction",
                        "object": {"text": instruction, "wait_time": wait_time}
                    })

                    # Update Repository for Persistence
                    BoxInspectionRepository.current_inspection_instruction = instruction
                    BoxInspectionRepository.current_wait_time = wait_time
                    BoxInspectionRepository.timer_start_time = datetime.now()

                    await box_log_service.add_box_log(
                        description=f"Starting With Inspection Sequence Number {sequence_number}",
                        box_id=box_id)

                    await box_log_service.add_box_log(
                        description=f"Updating Camera Position To {camera_position}",
                        box_id=box_id)

                    await inspection_box_manager.send_json({
                        "type": "camera_position",
                        "object": {"position": camera_position}
                    })

                    await box_log_service.add_box_log(
                        description=f"Waiting For {wait_time} Seconds...",
                        box_id=box_id)

                    await asyncio.sleep(wait_time)
                    # Check for Pause/Stop status
                    while True:
                        if BoxInspectionRepository.inspection_command == "Stopped":
                            await recorder.stop()
                            await inspection_box_manager.send_json({
                                "type": "recording_status",
                                "object": {"status": False}
                            })
                            await box_log_service.add_box_log(description="Inspection Stopped By User", box_id=box_id)
                            return
                        if BoxInspectionRepository.inspection_command == "Paused":
                            await asyncio.sleep(1)
                            if BoxInspectionRepository.inspection_command == "Stopped":
                                await recorder.stop()
                                await inspection_box_manager.send_json({
                                    "type": "recording_status",
                                    "object": {"status": False}
                                })
                                await box_log_service.add_box_log(description="Inspection Stopped By User",
                                                                  box_id=box_id)
                                return
                            continue
                        # If status is "Inspecting", proceed
                        break

                    is_suppressed = settings.IS_DEV and (suppress_cam_error if suppress_cam_error is not None else getattr(CameraRepository, 'suppress_camera_error', False))

                    stream = CameraRepository.stream_dict.get(camera_position)
                    frame = stream.get_recent_frame() if stream else None

                    if frame is None:
                        if not is_suppressed:
                            raise Exception(f"Camera stream not found or offline for position: {camera_position}")
                        frame = np.zeros((480, 640, 3), dtype=np.uint8)

                    success, buffer = cv2.imencode(".jpg", frame)
                    if not success:
                        if not is_suppressed:
                            raise Exception(f"Failed to encode frame from {camera_position}")
                        buffer = np.zeros((100,), dtype=np.uint8)

                    image_bytes = buffer.tobytes()
                    image_filename = f"inspection_sequence_{sequence_number}.jpeg"
                    image_path = os.path.join(box_obj.files_path, image_filename)
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)

                    await box_log_service.add_box_log(
                        description=f"Captured Frame From {camera_position}",
                        box_id=box_id)

                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            files = {"image": ("frame.jpg", image_bytes, "image/jpeg")}
                            data = {"box_id": box_id, "sequence_number": sequence_number, "lot_number": lot_number}

                            response = await client.post(
                                f"{settings.AI_SERVER_URL}inspect_box/m104",
                                data=data,
                                files=files
                            )
                            if response.status_code == 200:
                                result = response.json()
                                result_dict = json.loads(result['object']) if isinstance(result.get('object'), str) else result.get('object', {})
                                await BoxM104SequenceService.process_result(db, sequence_number, box_id, result_dict, box_log_service)
                            else:
                                raise Exception(f"AI Server returned status code {response.status_code}")
                    except Exception as ai_err:
                        if not is_suppressed:
                            raise Exception(f"AI Analysis failed for sequence #{sequence_number}: {ai_err}")
                        print(f"M104 AI/Camera analysis bypassed/mocked ({ai_err})")
                        mock_result = {
                            "UNIV": True,
                            "BOX_NO_VALID": True,
                            "FUZE 117": True,
                            "AV_MASS_KG_18_70": True,
                            "BOX_NUMBER": sequence_number,
                            "TO": True,
                            "COMMANDANT": True,
                            "CADPULOAON": True,
                            "FROM": True,
                            "CCN": True,
                            "OFBL": True,
                            "SEAL": True
                        }
                        await BoxM104SequenceService.process_result(db, sequence_number, box_id, mock_result, box_log_service)

                    await box_log_service.add_box_log(
                        description=f"Completed Inspection Sequence Number {sequence_number}",
                        box_id=box_id)

                # Finalize Success
                await recorder.stop()
                await inspection_box_manager.send_json({
                    "type": "recording_status",
                    "object": {"status": False}
                })
                from repositories.current_inspection_repositories import BoxInspectionRepository
                BoxInspectionRepository.recording_status = False
                await inspection_box_manager.send_json({
                    "type": "box_update",
                    "object": {
                        "box_number": box_obj.box_number,
                        "box_id": box_id,
                        "inspection_status": "Completed"
                    }
                })
                
                # Check acceptance status based on parameters
                inspection_obj = db.exec(select(BoxM104Inspection).where(BoxM104Inspection.id == box_obj.box_m104_inspection_id)).first()
                if inspection_obj:
                    parameters = [getattr(inspection_obj, c.name) for c in inspection_obj.__table__.columns if c.name != "id"]
                    if False in parameters:
                        box_obj.acceptance_status = False
                    elif all(p is True for p in parameters):
                        box_obj.acceptance_status = True
                    else:
                        box_obj.acceptance_status = None
                        
                box_obj.box_inspection_status = "Completed"
                box_obj.end_time = datetime.now()
                db.add(box_obj)
                db.commit()
                await box_log_service.add_box_log(
                    description=f"Completed Inspection For Box Sequence Number {box_obj.sequence_number}",
                    box_id=box_id)
                await inspection_box_manager.send_json({
                    "type": "instruction",
                    "object": {"text": "Please Check The Parameters And Continue", "wait_time": 0}
                })

            except Exception as e:
                db.rollback()
                print(f"Error in start_m104_inspection: {e}")
                await recorder.stop()
                await inspection_box_manager.send_json({
                    "type": "recording_status",
                    "object": {"status": False}
                })
                from repositories.current_inspection_repositories import BoxInspectionRepository
                BoxInspectionRepository.recording_status = False

                box_obj.box_inspection_status = "Failed"
                db.add(box_obj)
                db.commit()

                await box_log_service.add_box_log(
                    description=f"Inspection failed: {str(e)}",
                    box_id=box_id)

                await inspection_box_manager.send_json({
                    "type": "box_update",
                    "object": {
                        "box_number": box_obj.box_number,
                        "box_id": box_id,
                        "inspection_status": "Failed",
                        "description": f"Inspection failed: {str(e)}"
                    }
                })

                await inspection_box_manager.send_json({
                    "type": "instruction",
                    "object": {"text": "Inspection Failed To Continue Please Check The Camera Connections",
                               "wait_time": 0}
                })