#!/usr/bin/env bash
set -euo pipefail

echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo "Installing Docker..."
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

if command -v ufw >/dev/null 2>&1; then
  echo "Opening port 80 with UFW..."
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw --force enable
fi

echo "Docker version:"
docker --version

echo "VM setup complete. Log out and back in once to refresh group permissions."
