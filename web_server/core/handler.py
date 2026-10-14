from fastapi import Request
from core.exceptions import AppException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import HTTPException, RequestValidationError

templates = Jinja2Templates(directory="templates")


async def app_exception_handler(request: Request, exc: AppException):
    if exc.status_code == 401:
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return RedirectResponse(url="/auth/sign-in", status_code=303)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "message": exc.message,
            "object": None
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "message": exc.detail,
            "object": None
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": False,
            "message": "Internal server error",
            "object": None
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for err in exc.errors():
        print(err.get("loc", []))
        if "assigned_modules" in err.get("loc", []):
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Request Failed, Assigned Modules Must Be From 1 To 31",
                    "obj": None,
                    "status": False
                }
            )
        elif "email" in err.get("loc", []):
            return JSONResponse(status_code=400,
                content={
                    "message": "Request Failed, Email Address Invalid",
                    "obj": None,
                    "status": False
                })

    return JSONResponse(
        status_code=400,
        content={
            "message": "Validation Failed",
            "obj": None,
            "status": False
        }
    )

async def not_found_exception_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return templates.TemplateResponse(request=request, name="404.html", status_code=404)
    
    return JSONResponse(
        status_code=404,
        content={
            "status": False,
            "message": "Resource not found",
            "object": None
        }
    )