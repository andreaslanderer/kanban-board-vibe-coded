#!/usr/bin/env bash
set -euo pipefail

# ensure script runs from project root regardless of cwd
cd "$(dirname "$0")/.."

# Build Docker image and run container

echo "Building Docker image pm-app..."
docker build -t pm-app .

echo "Starting container pm-app on port 8000..."
docker run --rm -p 8000:8000 --env-file .env -d --name pm-app pm-app

echo "Container started. Access the app at http://localhost:8000/"
