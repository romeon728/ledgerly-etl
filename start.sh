#!/usr/bin/env bash
set -eo pipefail

echo "========================================================="
echo "   🚀 Starting Ledgerly ETL 2.0 (100% Local Stack)"
echo "========================================================="

# 1. Ensure .env file exists
if [ ! -f ".env" ]; then
    echo "📄 Creating local .env from template..."
    cp .env.example .env
fi

# Load env variables for checks
export $(grep -v '^#' .env | xargs)
VLLM_PORT=8000

# 2. Check if local vLLM Server is active
echo "🔍 Checking for active local vLLM instance..."
if python3 -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:${VLLM_PORT}/v1/models').getcode() == 200 else 1)" 2>/dev/null; then
    echo "✅ Local vLLM server is already running on port ${VLLM_PORT}!"
else
    echo "⚠️ Local vLLM server is not responding on http://127.0.0.1:${VLLM_PORT}."
    echo "   Starting vLLM using scripts/vllm_start.sh..."
    
    if [ -f "./scripts/vllm_start.sh" ]; then
        ./scripts/vllm_start.sh
    else
        echo "❌ Error: scripts/vllm_start.sh not found."
        exit 1
    fi
fi

# 3. Identify Podman/Docker Compose binary
COMPOSE_CMD=""
if podman compose version &> /dev/null; then
    COMPOSE_CMD="podman compose"
elif command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Error: Podman Compose is required to run Ledgerly."
    exit 1
fi
# 4. Build and start local database & web application
echo "📦 Spinning up Ledgerly Docker containers..."
$COMPOSE_CMD up -d --build

echo ""
echo "========================================================="
echo " 🎉 Ledgerly ETL 2.0 stack successfully initialized!"
echo "========================================================="
echo " 🌐 Web App UI:   http://localhost:8501"
echo " 🗄️ PostgreSQL:   localhost:5432"
echo " 🤖 Local vLLM:   http://localhost:8000/v1"
echo "========================================================="