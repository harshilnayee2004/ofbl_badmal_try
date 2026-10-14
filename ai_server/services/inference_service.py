import cv2
import json
import tempfile
import numpy as np
from repositories.processors_repository import ProcessorsRepository


class InferenceService:

    @staticmethod
    async def llm_raw_inference(image, prompt):
        qwen_engine=ProcessorsRepository.qwen_8b_model

        await image.seek(0)

        # Save image temporarily
        suffix = image.filename.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(await image.read())
            image_path = tmp.name

        result = qwen_engine.process_image(image_path,
            prompt
        )
        return result

    @staticmethod
    async def llm_text_raw_inference(prompt):
        qwen_engine = ProcessorsRepository.qwen_8b_model
        
        result = qwen_engine.process_text(prompt)
        return result

    @staticmethod
    async def rfdetr_raw_inference(image, inference_type):
        model = ProcessorsRepository.rfdetr_models[inference_type]

        await image.seek(0)
        contents = await image.read()

        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return json.dumps({"error": "Invalid image"})

        detection_list = model.process_image(frame)
        if inference_type == "safety_pin":
            if len(detection_list) == 0:
                return json.dumps({"SAFETY_PIN_PRESENCE": False})
            return json.dumps({"SAFETY_PIN_PRESENCE": True})
        if inference_type == "seals":
            if len(detection_list) == 2:
                return json.dumps({"SEALS": True})
            return json.dumps({"SEALS": False})
        elif inference_type == "C07_count":
            if len(detection_list) == 50:
                return json.dumps({"CONTAINER_COUNT_50":True})
            return json.dumps({"CONTAINER_COUNT_50":False})
        elif inference_type == "M104_count":
            return json.dumps({"BOX_COUNT":len(detection_list),"DETECTION_LIST":detection_list})
        elif inference_type == "bubble_predection":
            return detection_list
        else:
            return json.dumps({"error": "Invalid inference type"})