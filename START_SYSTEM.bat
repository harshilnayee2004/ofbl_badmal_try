@echo off
title MIPL AI Inspection System Launcher
color 0F
echo ================================================================
echo        Launching MIPL AI Inspection System...
echo ================================================================
echo.
echo [1/3] Starting AI Detection Server (Port 8000)...
start "MIPL AI Server [Port 8000]" cmd /k ""%~dp02_start_ai_server.bat""

echo [2/3] Waiting 4 seconds for AI Server to initialize...
timeout /t 4 /nobreak >nul

echo [3/3] Starting Web Server Dashboard (Port 8081)...
start "MIPL Web Server [Port 8081]" cmd /k ""%~dp03_start_web_server.bat""

timeout /t 2 /nobreak >nul
echo.
echo Opening browser to http://localhost:8081 ...
start http://localhost:8081

echo.
echo System started! Keep the two server terminal windows open while using.
echo Press any key to exit this launcher window.
pause >nul
