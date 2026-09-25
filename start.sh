#!/usr/bin/env bash
set -e

echo "🚀 Starting Ledgerly ETL Local Stack..."

# Check if docker-compose or compose plugin is installed
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Error: Docker Compose is required to run Ledgerly locally."
    exit 1
fi

# Build and start services in background
$COMPOSE_CMD up -d --build

echo "✅ Ledgerly is running!"
echo "🌐 Open your browser at: http://localhost:8501"