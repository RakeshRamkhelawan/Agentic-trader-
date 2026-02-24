# Agentic Trader Platform - Frontend Production Dockerfile
# Multi-stage build for optimized React app

# Stage 1: Build
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (use npm install instead of npm ci due to lockfile issues)
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Stage 2: Production with Nginx
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Default environment variables (can be overridden at runtime)
ENV VITE_API_URL=http://localhost:8003
ENV VITE_WS_URL=ws://localhost:8003/ws/public
ENV VITE_AUTH0_DOMAIN=
ENV VITE_AUTH0_CLIENT_ID=
ENV VITE_AUTH0_AUDIENCE=

# Create a script to generate runtime config and start nginx
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "Creating runtime config..."' >> /start.sh && \
    echo 'cat > /usr/share/nginx/html/config.js << EOF' >> /start.sh && \
    echo 'window.RUNTIME_CONFIG = {' >> /start.sh && \
    echo '  VITE_API_URL: "'"$VITE_API_URL"'",' >> /start.sh && \
    echo '  VITE_WS_URL: "'"$VITE_WS_URL"'",' >> /start.sh && \
    echo '  VITE_AUTH0_DOMAIN: "'"$VITE_AUTH0_DOMAIN"'",' >> /start.sh && \
    echo '  VITE_AUTH0_CLIENT_ID: "'"$VITE_AUTH0_CLIENT_ID"'",' >> /start.sh && \
    echo '  VITE_AUTH0_AUDIENCE: "'"$VITE_AUTH0_AUDIENCE"'"' >> /start.sh && \
    echo '};' >> /start.sh && \
    echo 'EOF' >> /start.sh && \
    echo 'cat /usr/share/nginx/html/config.js' >> /start.sh && \
    echo 'if ! grep -q "config.js" /usr/share/nginx/html/index.html; then' >> /start.sh && \
    echo '  sed -i '"'"'s|<head>|<head>\\n  <script src="./config.js"></script>|'"'"' /usr/share/nginx/html/index.html' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo 'exec nginx -g "daemon off;"' >> /start.sh && \
    chmod +x /start.sh

# Start with the script
CMD ["/start.sh"]
