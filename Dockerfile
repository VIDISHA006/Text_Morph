# Text-morph Complete Application Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for faster build)
RUN apt-get update && apt-get install -y \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy and install Python dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (excluding large data files initially)
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY scripts/ ./scripts/
COPY *.py ./
COPY docker-entrypoint.sh ./

# Copy data directory (AI models) - this is the large part
COPY data/ ./data/

# Create necessary directories
RUN mkdir -p /app/logs /app/temp /app/uploads

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose ports for backend and frontend
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || curl -f http://localhost:8000/ || exit 1

# Start the complete application
CMD ["/app/docker-entrypoint.sh"]