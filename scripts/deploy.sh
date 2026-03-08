#!/usr/bin/env bash
# Full redeploy: build image, import to k3s (requires sudo), rollout, reconnect port-forward.
# Usage: bash scripts/deploy.sh

set -euo pipefail

export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"

echo "==> Building Docker image..."
docker build -t commerce-agent:latest .

echo "==> Saving image to /tmp/commerce-agent.tar..."
docker save commerce-agent:latest -o /tmp/commerce-agent.tar

echo "==> Importing into k3s containerd (needs sudo)..."
sudo k3s ctr images import /tmp/commerce-agent.tar

echo "==> Rolling out new deployment..."
kubectl rollout restart deployment commerce-agent
kubectl rollout status deployment commerce-agent --timeout=60s

echo "==> Restarting port-forward..."
pkill -f "port-forward.*commerce-agent" 2>/dev/null || true
sleep 2
nohup bash "$(dirname "$0")/port-forward-loop.sh" > /tmp/commerce-pf.log 2>&1 &
sleep 3

if curl -sf http://localhost:8012/api/health > /dev/null 2>&1; then
  echo "==> Deploy complete. Health check passed."
else
  echo "==> Deploy complete. Health check pending (port-forward may still be connecting)."
fi
