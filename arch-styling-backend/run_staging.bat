@echo off
REM ARCH API - staging server for QA, port 8011, settings from .env.staging
REM (template: deploy\staging.env.example). Dev tools on, rate limits off.
cd /d %~dp0
if not exist .env.staging (
  echo Missing .env.staging. Copy deploy\staging.env.example to .env.staging and fill it in.
  exit /b 1
)
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
if not exist models\face_landmarker.task python tools\download_model.py
set ARCH_ENV_FILE=%~dp0.env.staging
set ARCH_ENV=
if "%ARCH_STAGING_PORT%"=="" set ARCH_STAGING_PORT=8011
python -m uvicorn app.main:app --host 0.0.0.0 --port %ARCH_STAGING_PORT%
