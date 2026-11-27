@echo off
title RecruitAI Copilot - Master Launcher
color 0E

echo ============================================================
echo   RecruitAI Copilot - One-Click Launcher
echo   Starting Backend (FastAPI + MCP) and Frontend (React)
echo ============================================================
echo.

set ROOT_DIR=%~dp0

echo [Step 1/3] Spawning Backend Server in a new window...
start "RecruitAI Backend" cmd /c "cd /d ""%ROOT_DIR%"" && call run_backend.bat"

echo Waiting 5 seconds for Dual MCP servers & FastAPI to initialize...
timeout /t 5 /nobreak >nul

echo [Step 2/3] Spawning Frontend Dev Server in a new window...
start "RecruitAI Frontend" cmd /c "cd /d ""%ROOT_DIR%"" && call run_frontend.bat"

echo Waiting 3 seconds for Vite server...
timeout /t 3 /nobreak >nul

echo [Step 3/3] Opening browser at http://localhost:5173 ...
start http://localhost:5173

echo.
echo ============================================================
echo   RecruitAI Copilot is now running!
echo   - Web UI:       http://localhost:5173
echo   - Backend API:  http://localhost:8000
echo   - API Docs:     http://localhost:8000/docs
echo ============================================================
echo.
echo You can close this launcher window at any time.
pause
