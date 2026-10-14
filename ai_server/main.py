from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from services.server_service import ServerService
from fastapi.middleware.cors import CORSMiddleware
from controllers.inference_controller import router as inference_router
from controllers.counting_controller import router as counting_controller
from controllers.inspect_box_controller import router as inspect_box_router
from controllers.inspect_fuze_controller import router as inspect_fuze_router
from inspection.router import router as inspection_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    await ServerService.startup_checks()
    yield
    await ServerService.shutdown_checks()


app = FastAPI(title="MIPL AI Inspection FastAPI Backend Engine.", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",      # Vite
        "http://localhost:8081"      # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(inference_router)
app.include_router(inspect_box_router)
app.include_router(inspect_fuze_router)
app.include_router(counting_controller)
app.include_router(inspection_router)
