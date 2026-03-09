#!/usr/bin/env bash
set -euo pipefail

# ensure script runs from project root
cd "$(dirname "$0")/.."

# Stop and remove the Docker container if it's running

echo "Stopping container pm-app..."
docker stop pm-app || true
docker rm pm-app || true

echo "Container stopped."
