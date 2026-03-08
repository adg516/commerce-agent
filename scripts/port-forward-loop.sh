#!/usr/bin/env bash
# Auto-reconnecting port-forward for commerce-agent.
# Usage: nohup bash scripts/port-forward-loop.sh &

export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
SERVICE="service/commerce-agent"
LOCAL_PORT=8012
REMOTE_PORT=80

while true; do
  echo "[$(date)] Starting port-forward on $LOCAL_PORT -> $SERVICE:$REMOTE_PORT"
  kubectl port-forward --address 0.0.0.0 "$SERVICE" "$LOCAL_PORT:$REMOTE_PORT" 2>&1
  echo "[$(date)] Port-forward exited, reconnecting in 3s..."
  sleep 3
done
