from fastapi.templating import Jinja2Templates
from schemas.response_schema import ResponseDTO
from services.inference_service import InferenceService
from fastapi import APIRouter, UploadFile, File, Form, Request

router = APIRouter(
    prefix="/inference",
    tags=["Lots"]
)

templates = Jinja2Templates(directory="templates")

@router.get("/check")
async def get_prompt_check_page(request: Request):
    return templates.TemplateResponse(request=request, name="prompt-check.html")

@router.get("/chat")
async def get_chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")

@router.post("/chat")
async def chat_inference(prompt: str = Form(...)):
    result = await InferenceService.llm_text_raw_inference(prompt)
    return ResponseDTO(message="Response generated successfully", status=True, object=result)

@router.post("")
async def start_inspection(
    image: UploadFile = File(...),
    prompt: str = Form(...)
):
    result=await InferenceService.llm_raw_inference(image, prompt)
    print("=="*60)
    print(result)
    print("=="*60)
    return ResponseDTO(message="Lot Created Successfully",status=True,object=result)
