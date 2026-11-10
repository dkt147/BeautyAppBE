#!/usr/bin/env bash
# ARCH API · staging server for QA, port 8011, settings from .env.staging
# (template: deploy/staging.env.example). Dev tools on, rate limits off.
cd "$(dirname "$0")"
if [ ! -f .env.staging ]; then
  echo "Missing .env.staging. Copy deploy/staging.env.example to .env.staging and fill it in." >&2
  exit 1
fi
if [ ! -d .venv ]; then
  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
else
  source .venv/bin/activate
fi
[ -f models/face_landmarker.task ] || python tools/download_model.py
export ARCH_ENV_FILE="$PWD/.env.staging"
unset ARCH_ENV                      # staging comes from .env.staging
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${ARCH_STAGING_PORT:-8011}"
