@echo off
REM ARCH styling backend - Windows start script
cd /d %~dp0
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
if not exist models\face_landmarker.task python tools\download_model.py
REM Local runs default to dev, unless ARCH_ENV is set or .env sets it.
findstr /b "ARCH_ENV=" .env >nul 2>&1 || if "%ARCH_ENV%"=="" set ARCH_ENV=dev
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
