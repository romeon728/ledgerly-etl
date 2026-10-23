#!/usr/bin/env bash
set -eo pipefail

echo "🔨 Building Ledgerly Standalone Linux Executable..."

# Ensure we are running from project root
cd "$(dirname "$0")/.."

# Run PyInstaller with Linux GUI integration flags
pyinstaller --noconfirm --onefile --windowed \
    --hidden-import=gi \
    --collect-all=gi \
    --collect-all=webview \
    --name "Ledgerly" \
    desktop_app.py

echo ""
echo "========================================================="
echo " 🎉 Build complete! Binary located at: ./dist/Ledgerly"
echo "========================================================="