# Kubernetes Architecture

## Cluster Setup

- Managed via Amazon EKS
- Multi-AZ deployment

## Node Groups

| Type | Purpose |
|------|--------|
| General | API + backend |
| GPU | AI workloads |
| Spot | Cost optimization |

---

## Add-ons

- AWS Load Balancer Controller
- Cluster Autoscaler
- Metrics Server
- External DNS

---

## Service Mesh

- Istio
  - Traffic routing
  - Canary deployments
  - mTLS

---

## Scaling

- HPA (CPU/memory)
- KEDA (queue-based)