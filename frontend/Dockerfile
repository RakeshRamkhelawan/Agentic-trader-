# =============================================================================
# AGENTIC TRADER - FRONTEND PRODUCTION DOCKERFILE
# Multi-stage build with Nginx - Consolidated Version
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build
# -----------------------------------------------------------------------------
# Use Debian-based slim image for better compatibility with native modules
FROM node:20-slim AS builder

WORKDIR /app

# Install build essentials for native modules
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./

# Install dependencies with high memory limit and legacy-peer-deps for stability
# This resolves recorded ERESOLVE conflicts between React 19 and Storybook.
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm install --legacy-peer-deps --no-audit --no-fund

# Copy source code
COPY . .

# Build the application
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Production (Nginx)
# -----------------------------------------------------------------------------
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create health check endpoint
RUN echo '<!DOCTYPE html><html><body>OK</body></html>' > /usr/share/nginx/html/health

# Expose ports
EXPOSE 80

# Default environment variables (can be overridden at runtime)
ENV VITE_API_URL=http://localhost:8003
ENV VITE_WS_URL=ws://localhost:8003/ws/public
ENV VITE_AUTH0_DOMAIN=
ENV VITE_AUTH0_CLIENT_ID=
ENV VITE_AUTH0_AUDIENCE=

# Create a script to generate runtime config and start nginx
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "Creating runtime config from environment..."' >> /start.sh && \
    echo 'cat > /usr/share/nginx/html/config.js << EOF' >> /start.sh && \
    echo 'window.RUNTIME_CONFIG = {' >> /start.sh && \
    echo '  VITE_API_URL: "$VITE_API_URL",' >> /start.sh && \
    echo '  VITE_WS_URL: "$VITE_WS_URL",' >> /start.sh && \
    echo '  VITE_AUTH0_DOMAIN: "$VITE_AUTH0_DOMAIN",' >> /start.sh && \
    echo '  VITE_AUTH0_CLIENT_ID: "$VITE_AUTH0_CLIENT_ID",' >> /start.sh && \
    echo '  VITE_AUTH0_AUDIENCE: "$VITE_AUTH0_AUDIENCE"' >> /start.sh && \
    echo '};' >> /start.sh && \
    echo 'EOF' >> /start.sh && \
    echo 'cat /usr/share/nginx/html/config.js' >> /start.sh && \
    echo 'if ! grep -q "config.js" /usr/share/nginx/html/index.html; then' >> /start.sh && \
    echo '  sed -i '"'"'s|<head>|<head>\\n  <script src="./config.js"></script>|'"'"' /usr/share/nginx/html/index.html' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo 'exec nginx -g "daemon off;"' >> /start.sh && \
    chmod +x /start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start with the script
CMD ["/start.sh"]
