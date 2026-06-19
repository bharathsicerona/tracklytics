#!/bin/bash
# start.sh — Tracklytics startup script
# Activates the virtual environment and launches the app.
# This is called by the LaunchAgent on Mac login.

cd /Users/bharathsicerona/Claude/Projects/Tracklytics
source venv/bin/activate
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
