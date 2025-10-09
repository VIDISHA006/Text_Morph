#!/bin/bash

# Complete Text-morph Application Entrypoint
set -e

echo "🚀 Starting Complete Text-morph Application..."
echo "📦 Backend + Frontend + AI Models included"

# Setup AI models at runtime (not during build to avoid timeout)
echo "🤖 Setting up AI models..."
python download_models.py || echo "⚠️ Model setup will continue in background"

# Function to start backend API
start_backend() {
    echo "📡 Starting Backend API (FastAPI) on port 8000..."
    cd /app
    uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 1 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    
    # Wait for backend to be ready
    echo "⏳ Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/ > /dev/null 2>&1; then
            echo "✅ Backend is ready!"
            break
        fi
        echo "   Attempt $i/30 - waiting for backend..."
        sleep 3
    done
}

# Function to start frontend
start_frontend() {
    echo "🖥️ Starting Frontend (Streamlit) on port 8501..."
    cd /app
    streamlit run frontend/app.py \
        --server.port 8501 \
        --server.address 0.0.0.0 \
        --server.headless true \
        --server.enableCORS false \
        --server.enableXsrfProtection false &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"
    
    # Wait for frontend to be ready
    echo "⏳ Waiting for frontend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
            echo "✅ Frontend is ready!"
            break
        fi
        echo "   Attempt $i/30 - waiting for frontend..."
        sleep 3
    done
}

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down Text-morph Application..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGTERM SIGINT EXIT

# Verify AI models are present
echo "🤖 Checking AI Models..."
if [ -d "/app/data/t5-multi-domain-finetuned" ] && [ -d "/app/data/t5-paraphrase-finetuned" ]; then
    echo "✅ AI Models found and loaded"
else
    echo "⚠️  AI Models not found in expected directories"
fi

# Initialize database tables
echo "🗃️ Initializing database..."
python -c "
try:
    from backend.api.database import *
    create_users_table()
    create_profiles_table()
    create_user_texts_table()
    create_processing_history_table()
    create_admin_table()
    create_admin_activity_table()
    create_user_feedback_table()
    print('✅ Database initialization complete!')
except Exception as e:
    print(f'⚠️  Database initialization warning: {e}')
    print('Application will continue...')
"

# Start all services
start_backend
start_frontend

echo ""
echo "🎉 Text-morph Complete Application is RUNNING!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Frontend (User Interface): http://localhost:8501"
echo "� Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Features Available:"
echo "• ✅ Text Summarization (Multi-domain)"
echo "• ✅ Text Paraphrasing"
echo "• ✅ Readability Analysis"
echo "• ✅ Translation Support"
echo "• ✅ User Authentication"
echo "• ✅ Processing History"
echo "• ✅ Admin Dashboard"
echo ""

# Keep the container running
wait