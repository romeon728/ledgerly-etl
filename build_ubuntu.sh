#!/usr/bin/env bash
set -eo pipefail

echo "🔨 Building Ledgerly Standalone Ubuntu Executable..."

# Run PyInstaller with GTK hidden imports and collected assets
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