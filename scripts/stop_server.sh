#!/bin/bash
PID_FILE="/home/ubuntu/Loker/logs/server.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Menghentikan Loker API Server (PID: $PID)..."
        kill "$PID"
        rm -f "$PID_FILE"
        echo "Server berhasil dihentikan."
        exit 0
    else
        rm -f "$PID_FILE"
        echo "PID file ditemukan tetapi proses tidak aktif."
        exit 0
    fi
else
    echo "Loker server tidak sedang berjalan."
fi
