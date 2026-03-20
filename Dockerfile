# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.8

### Builder stage: install dependencies and prepare environment
FROM python:${PYTHON_VERSION} AS builder

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy pyproject.toml and install dependencies directly
COPY pyproject.toml ./

# Install Python dependencies directly from pyproject.toml to avoid hash conflicts
RUN uv pip install --no-cache --prefix=/install . \
    && find /install -name "*.pyc" -delete \
    && find /install -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Copy application files
COPY . .

# Pre-download and cache the FinBERT model during build
# This reduces startup time and ensures the model is available
ENV HF_HOME="/app/.cache/huggingface"
ENV TRANSFORMERS_CACHE="/app/.cache/huggingface/transformers"

# Create cache directory and set permissions
RUN mkdir -p /app/.cache/huggingface/transformers

# Pre-load the model with retry logic for rate limiting
# Set PYTHONPATH to include installed packages before running preload script
RUN PYTHONPATH="/install/lib/python3.12/site-packages:/app" python preload_model.py

# Clean up unnecessary files to reduce image size
RUN rm -rf /app/preload_model.py \
    && find /app -name "*.pyc" -delete \
    && find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

### Final stage: lean runtime image
FROM python:${PYTHON_VERSION}-slim AS runtime

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Create app directory and set ownership
RUN mkdir -p /app && chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy installed Python dependencies from builder stage
COPY --from=builder /install /usr/local

# Copy only necessary application files from builder (exclude cache to avoid duplication)
COPY --from=builder --chown=appuser:appuser /app/server.py /app/
COPY --from=builder --chown=appuser:appuser /app/__init__.py /app/
COPY --from=builder --chown=appuser:appuser /app/mcp_health_check.py /app/

# Copy cached Hugging Face models from builder to user cache directory
COPY --from=builder --chown=appuser:appuser /app/.cache /home/appuser/.cache

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH="/usr/local/bin:$PATH"
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV STAGE=MAINNET
ENV LOG_LEVEL=INFO
ENV HF_HOME=/home/appuser/.cache/huggingface
# Keep cache path explicit so transformers reliably finds preloaded artifacts.
ENV TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface/transformers
# Force transformers to use offline mode - prevents any Hugging Face API calls
ENV TRANSFORMERS_OFFLINE=1

# Health check to ensure server and model are ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose port (uses PORT environment variable with default)
EXPOSE ${PORT:-8080}

# Run the application
CMD ["python", "server.py"] 