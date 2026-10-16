@echo off
title MIPL Web Dashboard Server (Port 8081)
color 0E
echo ================================================================
echo        Starting MIPL Web Dashboard Server on Port 8081...
echo ================================================================
cd /d "%~dp0web_server"
python -m uvicorn main:app --host 0.0.0.0 --port 8081 --reload
pause
