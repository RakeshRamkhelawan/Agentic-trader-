# VedAstro C# Bridge Dockerfile
#
# This Dockerfile sets up a container with:
# - .NET 8.0 runtime for VedAstro C# calculations
# - Python 3.13 with pythonnet for interop
# - Mono for Linux compatibility
#
# Build:
#   docker build -f infrastructure/docker/vedastro.Dockerfile -t vedastro-bridge .
#
# Run:
#   docker run -p 5000:5000 vedastro-bridge

FROM mcr.microsoft.com/dotnet/runtime:8.0 AS dotnet-base

# Install Python and dependencies
FROM python:3.13-slim AS python-base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    clang \
    libglib2.0-dev \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Mono (required for pythonnet on Linux)
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    dirmngr \
    gnupg \
    ca-certificates \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
    && echo "deb https://download.mono-project.com/repo/debian stable-buster main" | tee /etc/apt/sources.list.d/mono-official-stable.list \
    && apt-get update \
    && apt-get install -y mono-complete \
    && rm -rf /var/lib/apt/lists/*

# Copy .NET runtime from dotnet-base
COPY --from=dotnet-base /usr/share/dotnet /usr/share/dotnet
RUN ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet

# Set environment variables for pythonnet
ENV PYTHONNET_RUNTIME=coreclr
ENV DOTNET_ROOT=/usr/share/dotnet
ENV PYTHONNET_DLL_PATH=/app/libs/VedAstro.dll

# Install Python dependencies
COPY requirements/vedastro.txt /tmp/vedastro.txt
RUN pip install --no-cache-dir -r /tmp/vedastro.txt

# Create app directory
WORKDIR /app

# Copy VedAstro libraries
# NOTE: These must be downloaded from VedAstro releases
COPY libs/ /app/libs/

# Copy application code
COPY backend/vedastro/ /app/vedastro/
COPY backend/core/ /app/core/

# Create non-root user
RUN useradd -m -u 1000 vedastro && chown -R vedastro:vedastro /app
USER vedastro

# Expose HTTP API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run VedAstro HTTP bridge
CMD ["python", "-m", "vedastro.http_bridge"]
