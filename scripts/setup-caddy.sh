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
    reverse_proxy 127.0.0.1:8080
    tls $TLS_EMAIL
}
EOF

sudo systemctl enable caddy
sudo systemctl restart caddy

sudo ufw allow 80/tcp || true
sudo ufw allow 443/tcp || true
sudo ufw --force enable || true

echo "Checking local Caddy listener..."
sudo ss -ltnp | grep -E ':(80|443)' || true

echo "Waiting for HTTPS to come up..."
for attempt in $(seq 1 10); do
  if curl -fsS "https://$DOMAIN_NAME/health" >/tmp/caddy-health.out 2>/tmp/caddy-health.err; then
    cat /tmp/caddy-health.out
    exit 0
  fi
  echo "Attempt $attempt/10 failed. Retrying in 10s..."
  cat /tmp/caddy-health.err 2>/dev/null || true
  sudo journalctl -u caddy -n 40 --no-pager || true
  sleep 10
done

echo "HTTPS health check failed. This usually means ports 80/443 are not reachable from the internet."
echo "Check your Oracle Cloud security list / NSG rules and confirm the VM has a public IP."
sudo systemctl status caddy --no-pager || true
exit 1
