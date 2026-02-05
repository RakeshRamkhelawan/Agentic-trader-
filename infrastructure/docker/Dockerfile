# Use official lightweight Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/base.txt /app/requirements/base.txt

# Install dependencies from file
RUN pip install --no-cache-dir -r /app/requirements/base.txt

# Copy the application code
COPY . .

# Set Python path so backend module is found
ENV PYTHONPATH=/app

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "backend.main"]
