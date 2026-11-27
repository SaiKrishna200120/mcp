@echo off
title RecruitAI Copilot - Backend Server
color 0A

echo ============================================================
echo   Starting RecruitAI Copilot Backend & MCP Servers
echo ============================================================
echo.

cd /d "%~dp0backend"

:: Locate Python 3.10 executable or fallback to system python
set PYTHON_CMD="C:\Users\Sai Krishna\AppData\Local\Programs\Python\Python310\python.exe"
if not exist %PYTHON_CMD% (
    set PYTHON_CMD=python
)

echo [1/3] Using Python: %PYTHON_CMD%
echo [2/3] Launching FastAPI + Dual MCP Servers (candidate-tracker, resume-vault)...
echo [3/3] Serving on http://127.0.0.1:8000
echo.

%PYTHON_CMD% main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Backend process terminated with error code %ERRORLEVEL%.
    pause
)
