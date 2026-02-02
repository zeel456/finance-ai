# Optimized Dockerfile for Railway Free Tier (Under 4GB)
FROM python:3.11-slim

# Critical: Multi-stage build to reduce final image size
# Environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Use smaller torch index
    PIP_INDEX_URL=https://download.pytorch.org/whl/cpu \
    # Reduce transformers cache
    TRANSFORMERS_CACHE=/tmp/transformers_cache \
    SENTENCE_TRANSFORMERS_HOME=/tmp/sentence_transformers \
    HF_HOME=/tmp/huggingface \
    # Ensure Python packages are in PATH
    PATH="/home/appuser/.local/bin:$PATH"

# Install ONLY essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoclean

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# CRITICAL: Install PyTorch CPU-only version (much smaller)
# Install in specific order to minimize size
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    # Install PyTorch CPU-only (700MB instead of 2GB)
    pip install --no-cache-dir torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu && \
    # Install other ML packages - FIXED VERSION
    pip install --no-cache-dir \
        sentence-transformers==2.7.0 \
        transformers==4.41.2 \
        spacy==3.7.5 && \
    # Install remaining requirements (exclude torch, sentence-transformers, transformers, spacy)
    grep -v "torch==" requirements.txt | \
    grep -v "sentence-transformers==" | \
    grep -v "transformers==" | \
    grep -v "spacy==" | \
    pip install --no-cache-dir -r /dev/stdin && \
    # Download spaCy model (small version only)
    python -m spacy download en_core_web_sm --no-deps && \
    # Clean up pip cache aggressively
    rm -rf /root/.cache/pip/* && \
    # Remove unnecessary files from site-packages
    find /usr/local/lib/python3.11/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -type f -name "*.pyc" -delete && \
    find /usr/local/lib/python3.11/site-packages -type f -name "*.pyo" -delete && \
    find /usr/local/lib/python3.11/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Pre-download ONLY the small sentence transformer model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" && \
    # Clean transformers cache of unnecessary files
    find /tmp -type f -name "*.bin" -size +100M -delete 2>/dev/null || true

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads temp_files static/uploads /tmp/transformers_cache /tmp/sentence_transformers /tmp/huggingface && \
    chmod -R 755 uploads temp_files static

# Create non-root user BEFORE switching
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /tmp/transformers_cache /tmp/sentence_transformers /tmp/huggingface

# Switch to non-root user
USER appuser

# Expose port (Railway will use $PORT environment variable)
EXPOSE 10000

# MEMORY-OPTIMIZED gunicorn for Railway
# Use python -m to ensure gunicorn is found
CMD python -m gunicorn app:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 2 \
    --worker-class gevent \
    --worker-connections 500 \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 100 \
    --max-requests-jitter 20 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload
