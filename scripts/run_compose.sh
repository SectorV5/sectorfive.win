#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$ROOT_DIR"

docker compose build
# Ensure restart policies take effect on boot
docker compose up -d

echo "App is starting. Visit http://YOUR_SERVER_IP/"