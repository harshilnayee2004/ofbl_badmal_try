import json
from services.inference_service import InferenceService


class CountingService:

    @staticmethod
    async def count_C07_container(image):
        response = await InferenceService.rfdetr_raw_inference(image, "C07_count")
        return response

    @staticmethod
    async def count_M104_box(image):
        response = await InferenceService.rfdetr_raw_inference(image, "M104_count")
        return response
