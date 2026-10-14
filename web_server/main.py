import os
import asyncio
from sqlmodel import SQLModel
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from core.config import settings
from core.deps import get_current_user
from core.exceptions import AppException
from core.handler import app_exception_handler, not_found_exception_handler
from core.database import engine, SQLModel
from controllers.lot_controller import router as lot_router
from controllers.counting_controller import router as counting_router
from controllers.carrier_controller import router as carrier_router
from controllers.box_controller import router as box_router
from controllers.auth_controller import router as auth_router
from controllers.user_controller import router as user_router
from controllers.test_controller import router as test_router
from controllers.fuze_controller import router as fuze_router
from controllers.chat_controller import router as chat_router
from controllers.admin_controller import router as admin_router
from controllers.report_controller import router as report_router
from controllers.motor_controller import router as motor_router
from controllers.camera_controller import api_router as camera_api_router
from controllers.manage_user_controller import router as manage_user_router
from controllers.ptz_control_controller import router as ptz_control_router
from controllers.ai_server_controller import router as ai_server_router
from controllers.surveillance_controller import router as surveillance_router
from socket_controller.box_motor_socket_controller import box_motor_router
from socket_controller.fuze_motor_socket_controller import fuze_motor_router
from socket_controller.carrier_motor_socket_controller import carrier_motor_router
from socket_controller.box_log_socket_controller import router as box_log_router
from socket_controller.chat_socket_controller import router as chat_socket_router
from socket_controller.camera_status_socket_controller import camera_status_router
from socket_controller.fuze_log_socket_controller import router as fuze_log_router
from socket_controller.carrier_log_socket_controller import carrier_log_router
from socket_controller.lot_inspection_socket_controller import inspection_lot_router
from socket_controller.box_inspection_socket_controller import inspection_box_router
from socket_controller.fuze_inspection_socket_controller import inspection_fuze_router
from socket_controller.carrier_inspection_socket_controller import inspection_carrier_router
from socket_controller.admin_dashboard_socket_controller import admin_dashboard_router
from models.lot_model import Lot
from models.carrier_model import Carrier
from models.carrier_log_model import CarrierLog
from models.box_model import Box
from models.user_model import User
from models.fuze_model import Fuze
from models.camera_model import Camera
from models.box_log_model import BoxLog
from models.message_model import Message
from models.fuze_log_model import FuzeLog
from models.box_h2a_inspection_model import BoxH2AInspection
from models.carrier_6al_inspection_model import Carrier6ALInspection
from models.primer_1al_inspection_model import Primer1ALInspection
from models.box_G70_inspection_model import BoxG70Inspection
from models.box_M104_inspection_model import BoxM104Inspection
from services.startup_and_stop_service import startup_checks, stop_checks


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    startup_checks(engine)
    yield
    stop_checks(engine)


app = FastAPI(title="MIPL AI Inspection FastAPI Backend Engine.",lifespan=lifespan)

app.include_router(lot_router)
app.include_router(carrier_router)
app.include_router(box_router)
app.include_router(test_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(fuze_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(motor_router)
app.include_router(report_router)
app.include_router(counting_router)
app.include_router(camera_api_router)
app.include_router(manage_user_router)
app.include_router(ptz_control_router)
app.include_router(ai_server_router)
app.include_router(surveillance_router)
app.include_router(camera_status_router)

app.include_router(box_log_router)
app.include_router(fuze_log_router)
app.include_router(carrier_log_router)
app.include_router(box_motor_router)
app.include_router(fuze_motor_router)
app.include_router(carrier_motor_router)
app.include_router(chat_socket_router)
app.include_router(camera_status_router)
app.include_router(inspection_box_router)
app.include_router(inspection_lot_router)
app.include_router(inspection_fuze_router)
app.include_router(inspection_carrier_router)
app.include_router(admin_dashboard_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs(settings.LOT_DETAILS_PATH, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.LOT_DETAILS_PATH), name="media")

# Register Exception
app.add_exception_handler(AppException, app_exception_handler) # type: ignore
# app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(404, not_found_exception_handler)



@app.get("/")
def root(request: Request):
    # Try to check if user is logged in (via cookie)
    token = request.cookies.get("access_token")
    if token:
         return RedirectResponse(url="/home")
    
    return RedirectResponse(url="/auth/sign-in")

@app.get("/home")
def home_redirect(current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        return RedirectResponse(url="/admin/dashboard")
    elif current_user.role == "surveillance":
        return RedirectResponse(url="/surveillance/")
    else:
        return RedirectResponse(url="/user/dashboard")
