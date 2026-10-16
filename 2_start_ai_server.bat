@echo off
title MIPL AI Detection Server (Port 8000)
color 0B
echo ================================================================
echo        Starting MIPL AI Detection Server on Port 8000...
echo ================================================================
cd /d "%~dp0ai_server"
if exist "C:\Users\admin\.conda\envs\ofbl_ai\python.exe" (
    echo [Environment] Using conda env: ofbl_ai
    "C:\Users\admin\.conda\envs\ofbl_ai\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo [Environment] Using system python...
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
)
pause
