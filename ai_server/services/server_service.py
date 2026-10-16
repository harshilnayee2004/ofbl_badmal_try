import asyncio
from processors.rfdetr_processor import RFDETRProcessor
from repositories.processors_repository import ProcessorsRepository
from processors.qwenVLM8b_processor import QwenVLM8BProcessor


class ServerService:

    @staticmethod
    async def startup_checks():
        print("startup checks: initializing services...")
        asyncio.create_task(ServerService._load_qwen())

    @staticmethod
    async def _load_qwen():
        try:
            print("Loading Qwen 8B model in background...")
            loop = asyncio.get_running_loop()
            ProcessorsRepository.qwen_8b_model = await loop.run_in_executor(None, QwenVLM8BProcessor)
            print("Qwen 8B model loaded successfully and assigned to ProcessorsRepository.qwen_8b_model")
        except Exception as e:
            print(f"[Warning] Could not load Qwen 8B model: {e}")

    @staticmethod
    async def shutdown_checks():
        print("shutdown checks")
