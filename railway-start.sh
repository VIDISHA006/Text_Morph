#!/bin/bash
# Railway startup script for Text Morph AI
# This ensures proper service startup on Railway platform

echo "🚀 Starting Text Morph AI on Railway..."

# Set environment variables for Railway
export PORT=${PORT:-8000}
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8501}

# Start the application using docker-entrypoint.sh
exec ./docker-entrypoint.sh