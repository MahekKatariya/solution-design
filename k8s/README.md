# Kubernetes Manifests

This directory contains Kubernetes manifests for deploying the demo application with a complete observability stack using GitOps principles with ArgoCD.

## Directory Structure

```
k8s/
├── argocd/
│   └── bootstrap/
│       └── application.yaml    # ArgoCD Application for demo-app
└── demo-app/
    ├── app-deployment.yaml     # Demo application Deployment and Service
    ├── lgtm.yaml              # LGTM observability stack (Loki-Grafana-Tempo-Mimir)
    └── promptail-application.yaml  # Promtail Helm chart for log collection
```

## Prerequisites

Before deploying, ensure you have the following installed and configured:

| Tool | Version | Purpose |
|------|---------|---------|
| kubectl | >= 1.28 | Kubernetes CLI |
| helm | >= 3.12 | Package manager |
| Kubernetes cluster | >= 1.28 | Target cluster |

### Cluster Requirements

- A running Kubernetes cluster (EKS, GKE, AKS, or local like kind/minikube)
- `kubeconfig` configured with cluster admin access
- Default storage class available for persistent volumes (if needed)

## Quick Start

### Step 1: Install ArgoCD

```bash
# Create argocd namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=600s deployment/argocd-server -n argocd
```

### Step 2: Access ArgoCD UI

```bash
# Get the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port-forward to access the UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Access the ArgoCD UI at: https://localhost:8080

- **Username:** admin
- **Password:** (from the command above)

### Step 3: Deploy the Bootstrap Application

```bash
# Apply the bootstrap application to start the GitOps sync
kubectl apply -f k8s/argocd/bootstrap/application.yaml
```

This will create the `demo-app` Application in ArgoCD, which will automatically sync:
- The LGTM observability stack in the `observibility` namespace
- The demo-app deployment in the `default` namespace
- The Promtail daemon for log collection

### Step 4: Add Promtail Helm Repository

Since Promtail is deployed as a Helm chart, add the Grafana Helm repository:

```bash
# Add Grafana Helm repository
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Step 5: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n observibility
kubectl get pods -n default

# Check services
kubectl get svc -n observibility
kubectl get svc -n default
```

Expected output:

```
# observibility namespace
NAME                    READY   STATUS    RESTARTS   AGE
lgtm-xxx                1/1     Running   0          2m
promtail-xxx            1/1     Running   0          2m

# default namespace  
NAME                    READY   STATUS    RESTARTS   AGE
demo-app-xxx            1/1     Running   0          2m
```

## Components

### Demo Application

A FastAPI application with OpenTelemetry instrumentation:

| Property | Value |
|----------|-------|
| Image | `ghcr.io/blueswen/fastapi-observability/app:latest` |
| Port | 8000 |
| OTLP Endpoint | `http://lgtm.observibility:4317` |

### LGTM Stack

The LGTM (Loki-Grafana-Tempo-Mimir) stack provides full observability:

| Component | Port | Purpose |
|-----------|------|---------|
| Grafana | 3000 | Dashboards and visualization |
| OTLP gRPC | 4317 | OpenTelemetry telemetry ingestion |
| OTLP HTTP | 4318 | OpenTelemetry telemetry ingestion |
| Prometheus | 9090 | Metrics storage and querying |
| Loki | 3100 | Log aggregation |

### Promtail

Log collector that ships Kubernetes logs to Loki:

- Scrapes logs from all Kubernetes pods
- Enriches logs with pod labels and namespace metadata
- Forwards logs to Loki at `http://lgtm.observibility:3100/loki/api/v1/push`

## Accessing Services

### Grafana Dashboard

```bash
# Port-forward Grafana
kubectl port-forward svc/lgtm -n observibility 3000:3000
```

Access Grafana at: http://localhost:3000

### Demo Application

```bash
# Port-forward demo-app
kubectl port-forward svc/demo-app 8000:8000
```

Access the demo app at: http://localhost:8000

### Generate Telemetry Data

```bash
# Send requests to generate traces and metrics
curl http://localhost:8000
```

## Manual Deployment (Without ArgoCD)

If you prefer to deploy without ArgoCD:

```bash
# Create observability namespace first
kubectl apply -f k8s/demo-app/lgtm.yaml

# Wait for LGTM to be ready
kubectl wait --for=condition=available --timeout=300s deployment/lgtm -n observibility

# Deploy the demo application
kubectl apply -f k8s/demo-app/app-deployment.yaml

# Install Promtail manually with Helm
helm install promtail grafana/promtail \
  --namespace observibility \
  --set config.clients[0].url=http://lgtm.observibility:3100/loki/api/v1/push
```

## Troubleshooting

### ArgoCD Application Not Syncing

```bash
# Check ArgoCD application status
argocd app get demo-app

# Force refresh
argocd app sync demo-app
```

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check logs
kubectl logs <pod-name> -n <namespace>
```

### No Telemetry Data in Grafana

1. Verify the demo-app is sending telemetry:
   ```bash
   kubectl logs -l app=demo-app -n default
   ```

2. Verify LGTM is receiving data:
   ```bash
   kubectl logs -l app=lgtm -n observibility
   ```

3. Check Prometheus targets in Grafana:
   - Navigate to Explore → Prometheus
   - Check if `demo-app` target is up

## Setting Up SLI and Alerts in Grafana

### SLI: 95th Percentile Latency

This SLI measures the 95th percentile request latency for the demo-app. The following PromQL query calculates this metric:

```promql
histogram_quantile(0.95, sum by(le) (rate(fastapi_requests_duration_seconds_bucket{job="demo-app"}[5m])))
```

**What this query does:**
- `rate(...[5m])` - Calculates the per-second rate of request duration buckets over 5 minutes
- `sum by(le)` - Aggregates buckets across all instances while preserving the `le` (less than or equal) label
- `histogram_quantile(0.95, ...)` - Calculates the 95th percentile latency

### Create a Grafana Dashboard Panel

1. Access Grafana at http://localhost:3000
2. Navigate to **Dashboards** → **New Dashboard**
3. Click **Add Visualization**
4. Select **Prometheus** as the data source
5. Enter the query:
   ```promql
   histogram_quantile(0.95, sum by(le) (rate(fastapi_requests_duration_seconds_bucket{job="demo-app"}[5m])))
   ```
6. Set the panel title to "Request Latency (p95)"
7. Configure the Y-axis unit to **seconds**
8. Click **Apply** to save the panel

### Create an Alert Rule

To alert when p95 latency exceeds 0.3 seconds (300ms):

1. In Grafana, navigate to **Alerting** → **Alert rules**
2. Click **New alert rule**
3. Configure the alert:

   | Setting | Value |
   |---------|-------|
   | Rule name | HighLatencyP95 |
   | Data source | Prometheus |
   | Query | `histogram_quantile(0.95, sum by(le) (rate(fastapi_requests_duration_seconds_bucket{job="demo-app"}[5m])))` |

4. Set the condition:
   ```
   WHEN last() OF query(A) IS ABOVE 0.3
   ```

5. Configure evaluation behavior:
   - **Evaluate every:** 1m
   - **For:** 2m (pending period before firing)

6. Add notification settings:
   - **Contact point:** Select your notification channel (Slack, PagerDuty, etc.)
   - **Message:**
     ```
     High latency detected! P95 latency is {{ $values.A }} seconds, exceeding the 0.3s threshold.
     ```

7. Click **Save rule and exit**

### Alert Rule YAML (Alternative)

You can also define the alert rule as code in Grafana's provisioning:

```yaml
# Save as: grafana/provisioning/alerting/high-latency.yml
apiVersion: 1
groups:
  - name: demo-app-alerts
    interval: 1m
    rules:
      - uid: high-latency-p95
        title: HighLatencyP95
        condition: C
        data:
          - refId: A
            relativeTimeRange:
              from: 300
              to: 0
            datasourceUid: prometheus
            model:
              expr: histogram_quantile(0.95, sum by(le) (rate(fastapi_requests_duration_seconds_bucket{job="demo-app"}[5m])))
              refId: A
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions:
                - evaluator:
                    params:
                      - 0.3
                    type: gt
                  operator:
                    type: and
                  type: query
                  refId: A
        noDataState: NoData
        execErrState: Alerting
        for: 2m
        annotations:
          description: "P95 latency is {{ $values.A }}s, exceeding 0.3s threshold"
          summary: "High request latency detected"
```

### Verify the Alert

```bash
# Generate load to trigger the alert
for i in {1..100}; do
  curl http://localhost:8000 &
done
wait

# Check the alert status in Grafana
# Navigate to Alerting → Alert rules → HighLatencyP95
```

### Additional Useful Queries

| Metric | Query |
|--------|-------|
| P99 Latency | `histogram_quantile(0.99, sum by(le) (rate(fastapi_requests_duration_seconds_bucket{job="demo-app"}[5m])))` |
| P50 Latency | `histogram_quantile(0.50, sum by(le) (rate(fastapi_requests_duration_seconds_bucket{job="demo-app"}[5m])))` |
| Request Rate | `sum(rate(fastapi_requests_duration_seconds_count{job="demo-app"}[5m]))` |
| Error Rate | `sum(rate(fastapi_requests_duration_seconds_count{job="demo-app",status=~"5.."}[5m])) / sum(rate(fastapi_requests_duration_seconds_count{job="demo-app"}[5m]))` |

## Cleanup

```bash
# Delete applications from ArgoCD
kubectl delete -f k8s/argocd/bootstrap/application.yaml

# Delete all resources
kubectl delete namespace observibility
kubectl delete deployment demo-app
kubectl delete service demo-app

# Uninstall ArgoCD
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl delete namespace argocd
```