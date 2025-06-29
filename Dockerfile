FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and config files (using temp folders with proper permissions)
COPY api_temp/ ./api/
COPY backend_temp/ ./backend/
COPY system_temp/ ./system/
COPY config.py ./config.py
COPY .env.example ./.env.example

# Copy Angular build (ensure you have built it: ng build --prod)
COPY angular-ui/dist/ ./angular-ui/dist/

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=2 \
    CMD curl -f http://localhost:8000/system/status || exit 1

# Run the FastAPI app
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]