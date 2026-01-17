#!/bin/sh

SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

streamlit run $SCRIPT_DIR/../src/ledgerly/app.py