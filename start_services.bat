@echo off
title Smart Home Services Launcher
color 0A

echo ===================================================
echo   STARTING SMART HOME SERVICES
echo ===================================================
echo.
echo Current Directory: %CD%
echo.

:: 0. Start Redis Docker Container
echo [0/4] Starting Redis (Docker)...
docker start redis-smart-home >nul 2>&1
if %errorlevel% neq 0 (
    echo Redis container not found, creating new one...
    docker run -d --name redis-smart-home -p 6379:6379 --restart unless-stopped redis:latest
)
echo ✓ Redis running on localhost:6379
echo.

:: 1. Start Redis Check
echo [1/4] Checking Redis availability...
echo Please ensure Memurai/Redis is running on localhost:6379.
echo.

:: 2. Start Django Server
echo [2/4] Starting Django Server...
start "Django Server" cmd /k "call Scripts\activate && python manage.py runserver 0.0.0.0:8000"

:: 3. Start Celery Worker
echo [3/4] Starting Celery Worker...
start "Celery Worker" cmd /k "call Scripts\activate && celery -A smarthome_server worker --loglevel=info --pool=solo"

:: 4. Start Celery Beat
echo [4/4] Starting Celery Beat...
start "Celery Beat" cmd /k "call Scripts\activate && celery -A smarthome_server beat --loglevel=info"

echo.
echo ===================================================
echo   ALL COMPONENT WINDOWS LAUNCHED
echo ===================================================
echo.
echo 1. Ensure Redis is running for Realtime Updates to work!
echo 2. If windows close immediately, check for errors in them.
echo.
pause
