import cv2
import asyncio
import json
from core.config import Settings
from sentry_sdk.integrations import httpx
from services.ptz_control_service import PTZControlService
from repositories.camera_repositories import CameraRepository
from repositories.inspection_sequence_repositories import M104CountingSequence



class BoxM104InspectionService:

    @staticmethod
    async def start_counting():
      PTZControlService.control_roof_top_1(2290,27000,5443)
      

      sequence_list = M104CountingSequence.sequences
      box_count = 0
      for sequence in sequence_list:
        p = sequence.get('p')
        t = sequence.get('t')
        z = sequence.get('z')
        PTZControlService.control_roof_top_1(p,t,z)
        await asyncio.sleep(5)

        stream = CameraRepository.stream_dict.get("PRIMER_BOX_TOP")
        if not stream:
            raise Exception(f"Camera stream not found for position: PRIMER_BOX_TOP")

        frame = stream.get_recent_frame()
        if frame is None:
            raise Exception(f"Failed to capture frame from PRIMER_BOX_TOP")

        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            raise Exception(f"Failed to encode frame for M104 Counting")

        image_bytes = buffer.tobytes()
        # image_filename = f"inspection_sequence_{sequence_number}.jpeg"
        # image_path = os.path.join(fuze_obj.files_path, image_filename)
        # with open(image_path, "wb") as f:
        #     f.write(image_bytes)

        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"image": ("frame.jpg", image_bytes, "image/jpeg")}

            response = await client.post(
                f"{Settings.AI_SERVER_URL}count/M104",
                files=files
            )
            result = response.json()
            result_dict = json.loads(result['object'])
            print(result)
            print(result_dict)
            box_count+=result_dict['BOX_COUNT']
      PTZControlService.control_roof_top_1(2290,27000,5443)
      return box_count

      