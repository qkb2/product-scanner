#!/bin/bash

# Activate Python virtual environment (optional, if you use one)
# source /home/pi/venv/bin/activate

# Navigate to your project directory
cd "$(dirname "$0")"

# Load .env variables manually to ensure they are available in this shell
export $(grep -v '^#' .env | xargs)

# Run FastAPI app with uvicorn, using HTTPS if cert/key are defined
if [[ -n "$SSL_CERTFILE" && -n "$SSL_KEYFILE" ]]; then
    echo "Starting with HTTPS using certs from $SSL_CERTFILE and $SSL_KEYFILE"
    uvicorn edge_server:app \
        --host 0.0.0.0 \
        --port 8000 \
        --ssl-certfile "$SSL_CERTFILE" \
        --ssl-keyfile "$SSL_KEYFILE"
else
    echo "Starting with HTTP (no SSL certs provided)"
    uvicorn edge_server:app \
        --host 0.0.0.0 \
        --port 8000
fi
