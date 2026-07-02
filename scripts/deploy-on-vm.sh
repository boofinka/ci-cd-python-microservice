#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <image>"
  exit 1
fi

IMAGE="$1"

if [ -z "${GHCR_USERNAME:-}" ]; then
  echo "GHCR_USERNAME is required"
  exit 1
fi

if [ -z "${GHCR_TOKEN:-}" ]; then
  echo "GHCR_TOKEN is required"
  exit 1
fi

echo "Logging into GHCR..."
printf '%s' "$GHCR_TOKEN" | sudo docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin

echo "Pulling image $IMAGE..."
sudo docker pull "$IMAGE"

echo "Restarting container..."
sudo docker rm -f python-microservice >/dev/null 2>&1 || true
sudo docker run -d \
  --name python-microservice \
  --restart unless-stopped \
  -p 127.0.0.1:8080:8000 \
  "$IMAGE"

echo "Container status:"
sudo docker ps --filter "name=python-microservice"
