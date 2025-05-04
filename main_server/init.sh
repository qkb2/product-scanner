#!/bin/bash

# Optional: activate virtual environment
# source /path/to/venv/bin/activate

# Navigate to the directory of the script
cd "$(dirname "$0")"

# Load .env environment variables
export $(grep -v '^#' .env | xargs)

# Define default app path if not set
APP_MODULE=${APP_MODULE:-main_server.main:app}

# Run FastAPI app with or without SSL, depending on .env config
if [[ -n "$SSL_CERTFILE" && -n "$SSL_KEYFILE" ]]; then
    echo "Starting with HTTPS using certs from $SSL_CERTFILE and $SSL_KEYFILE"
    uvicorn "$APP_MODULE" \
        --host 0.0.0.0 \
        --port 8000 \
        --ssl-certfile "$SSL_CERTFILE" \
        --ssl-keyfile "$SSL_KEYFILE"
else
    echo "Starting with HTTP (no SSL certs provided)"
    uvicorn "$APP_MODULE" \
        --host 0.0.0.0 \
        --port 8000
fi
