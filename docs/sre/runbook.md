# Runbooks

## Service Down

1. Check Grafana dashboards
2. Check pod status
   kubectl get pods
3. Check logs
4. Restart deployment
5. Rollback via ArgoCD

---

## High Latency

1. Check DB performance
2. Check CPU/memory
3. Scale pods

---

## Queue Backlog

1. Check worker pods
2. Scale workers
3. Investigate failures