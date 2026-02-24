#!/bin/sh
# Docker Entrypoint for Frontend
# Replaces environment variables in the built files at runtime

set -e

echo "============================================================"
echo "Agentic Trader Frontend - Starting with Configuration"
echo "============================================================"

# Create runtime config from environment variables
cat > /usr/share/nginx/html/config.js << 'EOF'
window.RUNTIME_CONFIG = {
  VITE_API_URL: "${VITE_API_URL:-http://localhost:8003}",
  VITE_WS_URL: "${VITE_WS_URL:-ws://localhost:8003/ws/public}",
  VITE_AUTH0_DOMAIN: "${VITE_AUTH0_DOMAIN:-}",
  VITE_AUTH0_CLIENT_ID: "${VITE_AUTH0_CLIENT_ID:-}",
  VITE_AUTH0_AUDIENCE: "${VITE_AUTH0_AUDIENCE:-}"
};
EOF

# Replace placeholders with actual values
sed -i "s|\"\${VITE_API_URL:-http://localhost:8003}\"|\"${VITE_API_URL:-http://localhost:8003}\"|g" /usr/share/nginx/html/config.js
sed -i "s|\"\${VITE_WS_URL:-ws://localhost:8003/ws/public}\"|\"${VITE_WS_URL:-ws://localhost:8003/ws/public}\"|g" /usr/share/nginx/html/config.js
sed -i "s|\"\${VITE_AUTH0_DOMAIN:-}\"|\"${VITE_AUTH0_DOMAIN:-}\"|g" /usr/share/nginx/html/config.js
sed -i "s|\"\${VITE_AUTH0_CLIENT_ID:-}\"|\"${VITE_AUTH0_CLIENT_ID:-}\"|g" /usr/share/nginx/html/config.js
sed -i "s|\"\${VITE_AUTH0_AUDIENCE:-}\"|\"${VITE_AUTH0_AUDIENCE:-}\"|g" /usr/share/nginx/html/config.js

echo "Runtime configuration created:"
cat /usr/share/nginx/html/config.js

# Replace placeholder in index.html to load the config
if ! grep -q "config.js" /usr/share/nginx/html/index.html; then
  sed -i 's|<head>|<head>\n  <script src="./config.js"></script>|' /usr/share/nginx/html/index.html
fi

echo "============================================================"
echo "Starting Nginx..."
echo "============================================================"

# Start nginx
exec nginx -g "daemon off;"
