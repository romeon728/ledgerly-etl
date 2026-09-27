#!/usr/bin/env bash
set -eo pipefail

echo "========================================================="
echo "   🔄 Restarting Ledgerly Streamlit App Only..."
echo "========================================================="

# 1. Force-remove stale app container to prevent Podman name collisions
echo "🧹 Cleaning up existing app container..."
if command -v podman &> /dev/null; then
    podman rm -f ledgerly-app 2>/dev/null || true
elif command -v docker &> /dev/null; then
    docker rm -f ledgerly-app 2>/dev/null || true
fi

# 2. Identify Compose command
COMPOSE_CMD=""
if podman compose version &> /dev/null; then
    COMPOSE_CMD="podman compose"
elif command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

# 3. Rebuild and launch only the app service with forced recreation
if [ -n "$COMPOSE_CMD" ]; then
    echo "📦 Rebuilding and starting 'app' service with latest .env..."
    $COMPOSE_CMD up -d --build --force-recreate app
else
    echo "❌ Error: Neither podman compose nor docker compose was found."
    exit 1
fi

echo ""
echo "========================================================="
echo " ✨ Ledgerly UI successfully restarted!"
echo " 🌐 Web App UI: http://localhost:8501"
echo "========================================================="