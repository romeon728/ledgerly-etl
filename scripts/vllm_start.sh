#!/usr/bin/env bash
set -eo pipefail

# ---------------------------------------------------------
# Auto-activate Virtual Environment
# ---------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

MODEL="${VLLM_MODEL_NAME:-Qwen/Qwen2.5-3B-Instruct-AWQ}"
PORT="8000"
LOG_FILE="vllm_server.log"

echo "========================================================="
echo " 🤖 Starting Local vLLM Engine (Optimized for 8GB VRAM)"
echo " Model: $MODEL"
echo " Port:  $PORT"
echo " Environment: $(which python3)"
echo "========================================================="

# ---------------------------------------------------------
# Pre-Start Process Cleanup
# ---------------------------------------------------------
echo "🧹 Cleaning up lingering processes..."
pkill -9 -f "python.*vllm" || true
pkill -9 -f "VLLM::EngineCore" || true
pkill -9 -f "vllm serve" || true
sleep 3

unset VLLM_MODEL
unset VLLM_HOST
unset VLLM_ATTENTION_BACKEND
unset VLLM_SKIP_WARMUP

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export VLLM_USE_FLASHINFER_SAMPLER=0
export FLASHINFER_WORKSPACE_SIZE=0

if command -v vllm &> /dev/null; then
    CMD="vllm serve $MODEL"
elif python3 -c "import vllm" &> /dev/null; then
    CMD="python3 -m vllm.entrypoints.openai.api_server --model $MODEL"
else
    echo "❌ Error: vLLM is not installed in the active environment ($(which python3))."
    exit 1
fi

echo "🚀 Launching vLLM in background (logging to $LOG_FILE)..."
$CMD \
    --host 0.0.0.0 \
    --port $PORT \
    --gpu-memory-utilization 0.45 \
    --max-model-len 1024 \
    --enforce-eager \
    --quantization awq > "$LOG_FILE" 2>&1 &

VLLM_PID=$!

echo "⏳ Waiting for vLLM server on http://127.0.0.1:$PORT/v1/models..."

MAX_RETRIES=60
RETRY_COUNT=0

while true; do
    if ! kill -0 $VLLM_PID 2>/dev/null; then
        echo "❌ vLLM process exited unexpectedly. Check $LOG_FILE for details."
        exit 1
    fi

    # Explicitly check for HTTP 200 OK using Python
    if python3 -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:$PORT/v1/models').getcode() == 200 else 1)" 2>/dev/null; then
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Timed out waiting for vLLM to start."
        exit 1
    fi

    sleep 2
done

echo "========================================================="
echo "🎉 vLLM Server is UP and READY! (PID: $VLLM_PID)"
echo " API Base: http://127.0.0.1:$PORT/v1"
echo " Logs:     tail -f $LOG_FILE"
echo "========================================================="