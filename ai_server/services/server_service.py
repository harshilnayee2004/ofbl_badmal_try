from processors.rfdetr_processor import RFDETRProcessor
from repositories.processors_repository import ProcessorsRepository
# from processors.qwenVLM8b_L4_vllm_processor import QwenVLM8BProcessorVLLM


class ServerService:

    @staticmethod
    async def startup_checks():
        print("startup checks")
        # rfdetr_processor_safety_pin=RFDETRProcessor(r"/home/agx/servers/ai_server/ai_models/safety_pin_model.pth")
        # rfdetr_processor_C07_container_count=RFDETRProcessor(r"/home/agx/servers/ai_server/ai_models/C07_container_counting.pth")
        # rfdetr_processor_M104_box_count=RFDETRProcessor(r"/home/agx/servers/ai_server/ai_models/M104_box_counting.pth",threshold=0.6)
        # rfdetr_processor_bubble_prediction=RFDETRProcessor(r"./ai_models/bubble_prediction.pth",threshold=0.6,label="bubble")
        # rfdetr_processor_seals=RFDETRProcessor(r"/home/agx/servers/ai_server/ai_models/M104_seal.pth",threshold=0.6,label="seal")

        # rfdetr_processor = RFDETRProcessor()
        

        # ProcessorsRepository.rfdetr_models['safety_pin']=rfdetr_processor_safety_pin
        # ProcessorsRepository.rfdetr_models['C07_count'] = rfdetr_processor_C07_container_count
        # ProcessorsRepository.rfdetr_models['M104_count'] = rfdetr_processor_M104_box_count
        # ProcessorsRepository.rfdetr_models['rfdetr_processor'] = rfdetr_processor
        # ProcessorsRepository.rfdetr_models['bubble_prediction'] = rfdetr_processor_bubble_prediction
        # ProcessorsRepository.rfdetr_models['seals'] = rfdetr_processor_seals
        # qwen_engine=QwenVLM8BProcessorVLLM()
        # ProcessorsRepository.qwen_8b_model=qwen_engine

    @staticmethod
    async def shutdown_checks():
        print("shutdown checks")
