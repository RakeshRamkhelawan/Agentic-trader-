# Builder stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Create venv and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Command
CMD ["python", "-m", "backend.main"]
