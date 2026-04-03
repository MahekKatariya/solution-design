# CI/CD Architecture

## CI Pipeline (GitHub Actions)

Steps:
1. Lint
2. Unit tests
3. Build Docker image
4. Security scan
5. Push to ECR

---

## CD Pipeline (GitOps)

Flow:

GitHub → ArgoCD → Kubernetes

---

## Deployment Strategies

- Rolling updates
- Canary (Istio)
- Blue/Green

---

## Rollback

- ArgoCD rollback
- Previous image version

---

## Versioning

- Semantic Versioning (SemVer)