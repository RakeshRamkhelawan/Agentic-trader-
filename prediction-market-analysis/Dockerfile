# =============================================================================
# Prediction Market Intelligence Service - Dockerfile
# Multi-stage build voor optimale image size en security
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder - Compile dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies voor native extensions (numpy, pandas, web3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first voor Docker layer caching
COPY requirements.txt .

# Create virtual environment en install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# STAGE 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Image metadata
LABEL maintainer="Agentic Trader Platform"
LABEL description="Prediction Market Intelligence Service"
LABEL version="1.0.0"

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code with correct ownership
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup main.py /app/
COPY --chown=appuser:appgroup api_server.py /app/

# Create required directories
RUN mkdir -p /app/data /app/output /app/.cache && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment configuration
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expose API port
EXPOSE 8002

# Health check - verificeer dat API responsive is
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start API server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
