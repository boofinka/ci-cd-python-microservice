#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y || true

echo "Ensuring Docker is installed..."
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get install -y docker.io
else
  echo "Docker is already installed."
fi

sudo systemctl enable docker
sudo systemctl start docker

if ! id -nG "$USER" | tr ' ' '\n' | grep -qx 'docker'; then
  sudo usermod -aG docker "$USER"
  echo "Added $USER to the docker group. Log out and back in once to refresh permissions."
else
  echo "User already belongs to the docker group."
fi

if command -v ufw >/dev/null 2>&1; then
  echo "Opening required ports with UFW..."
  sudo ufw allow 22/tcp || true
  sudo ufw allow 80/tcp || true
  sudo ufw allow 443/tcp || true
  sudo ufw --force enable || true
fi

echo "Docker version:"
docker --version

echo "VM setup complete."
