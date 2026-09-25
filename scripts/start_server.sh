#!/bin/bash
PROJECT_DIR="/home/ubuntu/Loker"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
PID_FILE="$PROJECT_DIR/logs/server.pid"
LOG_FILE="$PROJECT_DIR/logs/server.log"

mkdir -p "$PROJECT_DIR/logs"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Loker server sudah berjalan (PID: $PID)."
        exit 0
    fi
fi

echo "Memulai Loker API Server pada port 8088..."
cd "$PROJECT_DIR"
PYTHONPATH=/home/ubuntu nohup "$VENV_PYTHON" -m uvicorn Loker.api.server:app --host 0.0.0.0 --port 8088 > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "Server berhasil dimulai (PID: $(cat "$PID_FILE")). Log: $LOG_FILE"
