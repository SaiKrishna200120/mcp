@echo off
title RecruitAI Copilot - Frontend Dev Server
color 0B

echo ============================================================
echo   Starting RecruitAI Copilot Frontend (React + Vite)
echo ============================================================
echo.

cd /d "%~dp0frontend"

echo [1/2] Checking frontend dependencies...
if not exist "node_modules\" (
    echo Installing node dependencies...
    call npm.cmd install
)

echo [2/2] Starting Vite development server on http://localhost:5173 ...
echo.

call npm.cmd run dev -- --host 127.0.0.1

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Frontend server terminated with error code %ERRORLEVEL%.
    pause
)
