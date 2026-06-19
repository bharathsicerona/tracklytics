#!/bin/bash
# Tracklytics — start locally
# Access at: http://localhost:8000  or  http://<your-mac-ip>:8000 (WiFi)

cd "$(dirname "$0")"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
