#!/bin/bash

# Railway-optimized Text Morph Entrypoint
set -e

echo "🚀 Starting Text Morph AI on Railway..."

# Get the PORT from Railway environment
PORT=${PORT:-8000}

# Start the simplified FastAPI backend
echo "📡 Starting Backend API on port $PORT..."
exec uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT --workers 1