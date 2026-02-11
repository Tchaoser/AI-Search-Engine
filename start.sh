#!/bin/sh
set -e

echo "Starting main API..."
uvicorn backend.main:app --host 0.0.0.0 --port 5000 &

echo "Starting frontend preview..."
cd /app/frontend
npm run preview -- --host 0.0.0.0 &

wait
