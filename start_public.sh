#!/bin/bash
# Tracklytics — start with public Cloudflare tunnel
# Share the tunnel URL with friends for remote access.
# Note: URL changes every time you restart this script.

cd "$(dirname "$0")"
source venv/bin/activate

# Start the app in the background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
APP_PID=$!

echo ""
echo "✅ Tracklytics started (PID $APP_PID)"
echo "⏳ Starting Cloudflare tunnel..."
echo ""

# Start the tunnel (stays in foreground — Ctrl+C stops everything)
trap "kill $APP_PID 2>/dev/null; exit" INT TERM
cloudflared tunnel --url http://localhost:8000

# If cloudflared exits, also stop the app
kill $APP_PID 2>/dev/null
