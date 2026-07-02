#!/bin/sh
# Build journery:latest and start/restart clipboard-demo on port 5053.
# Demo mode: all data lives in the visitor's browser (static/demo.js), so this
# container needs NO data volume — the server DB is unused.
set -e
cd /volume1/docker/journery-build

echo "Building journery:latest..."
docker build -t journery:latest . || { echo "Build failed"; exit 1; }

echo "Recreating clipboard-demo..."
docker stop clipboard-demo 2>/dev/null || true
docker rm   clipboard-demo 2>/dev/null || true
docker run -d \
  --name clipboard-demo \
  --restart unless-stopped \
  -p 5053:5000 \
  -e "JOURNERY_NAME=Demo" \
  -e "DEMO_MODE=1" \
  journery:latest

echo "Started: clipboard-demo → http://10.0.0.10:5053"
