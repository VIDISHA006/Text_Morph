# Multi-stage build for Railway optimization
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements-minimal.txt requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements-minimal.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create directory for SQLite database  
RUN mkdir -p /app/instance

# Expose ports for both services
EXPOSE 8000 8501

# Set environment for Railway
ENV RAILWAY=true
ENV PORT=8000
ENV STREAMLIT_SERVER_PORT=8501

# Use custom entrypoint to start both services
CMD ["./docker-entrypoint.sh"]