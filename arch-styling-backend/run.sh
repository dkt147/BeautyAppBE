#!/usr/bin/env bash
# ARCH styling backend - macOS / Linux start script
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
else
  source .venv/bin/activate
fi
[ -f models/face_landmarker.task ] || python tools/download_model.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
