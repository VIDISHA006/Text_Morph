# Ultra-lightweight Python image for Railway
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install only essential system dependencies
RUN apk add --no-cache \
    curl \
    bash \
    && rm -rf /var/cache/apk/*

# Copy and install minimal Python dependencies
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-minimal.txt

# Copy only essential application files (exclude large data/)
COPY backend/ backend/
COPY frontend/ frontend/  
COPY docker-entrypoint.sh .
COPY download_models.py .

# Make entrypoint executable and create directories
RUN chmod +x docker-entrypoint.sh && \
    mkdir -p /app/instance /app/data

# Expose ports
EXPOSE 8000 8501

# Environment variables for Railway
ENV RAILWAY=true \
    PORT=8000 \
    STREAMLIT_SERVER_PORT=8501 \
    PYTHONUNBUFFERED=1

# Start application
CMD ["./docker-entrypoint.sh"]