#!/usr/bin/env bash
set -euo pipefail

DOMAIN_NAME="${1:-}"
TLS_EMAIL="${2:-}"

if [ -z "$DOMAIN_NAME" ]; then
  echo "Usage: $0 <domain-name> [email]"
  exit 1
fi

if [[ "$DOMAIN_NAME" == *"example.com"* ]]; then
  echo "Please use a real, fresh domain name that is not already in use."
  exit 1
fi

if [ -z "$TLS_EMAIL" ]; then
  TLS_EMAIL="admin@$DOMAIN_NAME"
fi

if ! command -v caddy >/dev/null 2>&1; then
  echo "Installing Caddy..."
  sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
  sudo apt-get update
  sudo apt-get install -y caddy
fi

sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
$DOMAIN_NAME {
    reverse_proxy localhost:80
    tls $TLS_EMAIL
}
EOF

sudo systemctl enable caddy
sudo systemctl restart caddy

sudo ufw allow 443/tcp || true

sleep 5
curl -I "https://$DOMAIN_NAME/health" || true
