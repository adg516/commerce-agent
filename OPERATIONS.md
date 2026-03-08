# Commerce Agent — Operations Cheat Sheet

All commands assume you've SSH'd into the Pi and run:
```bash
export KUBECONFIG=~/.kube/config
```

---

## Diagnose

```bash
# Is the pod running?
kubectl get pods -l app=commerce-agent

# Pod logs (last 50 lines)
kubectl logs -l app=commerce-agent --tail=50

# Pod events (crash loops, image pull errors, OOM)
kubectl describe pod -l app=commerce-agent | tail -40

# Is the service wired up?
kubectl get svc commerce-agent

# Quick health check (from the Pi itself)
curl -s http://localhost:8012/api/health
```

---

## Expose (after SSH'ing back in)

The port-forward dies when you disconnect. Restart it:

```bash
# Foreground (stops when you Ctrl+C or disconnect)
kubectl port-forward --address 0.0.0.0 service/commerce-agent 8012:80

# Background (survives your shell, auto-reconnects)
nohup bash scripts/port-forward-loop.sh > /tmp/pf.log 2>&1 &
```

If you use Cloudflare Tunnel, the tunnel itself stays up — only the
port-forward target needs to be alive.

---

## Re-deploy (code changes)

```bash
# 1. Build
cd ~/commerce-agent
docker build -t commerce-agent:latest .
docker save commerce-agent:latest -o /tmp/commerce-agent.tar

# 2. Import + restart
sudo k3s ctr images import /tmp/commerce-agent.tar
kubectl rollout restart deployment commerce-agent

# 3. Wait for rollout
kubectl rollout status deployment commerce-agent

# 4. Restart port-forward
pkill -f "port-forward.*commerce-agent" 2>/dev/null
nohup bash scripts/port-forward-loop.sh > /tmp/pf.log 2>&1 &
```

Or use the all-in-one script (requires sudo password):
```bash
bash scripts/deploy.sh
```

---

## Restart without rebuilding

```bash
kubectl rollout restart deployment commerce-agent
kubectl rollout status deployment commerce-agent
```

---

## Nuke and recreate

```bash
kubectl delete deployment commerce-agent
kubectl delete svc commerce-agent
kubectl apply -f k8s/
```

---

## Cloudflare Tunnel

The tunnel runs as a systemd service. Check it with:
```bash
sudo systemctl status cloudflared
sudo systemctl restart cloudflared
```
