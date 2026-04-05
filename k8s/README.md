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

## Temporal Workflow Integration

This setup includes Temporal workflow engine integration for building reliable, scalable distributed applications.

### Temporal Components

The Temporal integration includes:

| Component | Description | Port |
|-----------|-------------|------|
| Temporal Server | Core workflow engine | 7233 |
| Temporal Web UI | Dashboard for workflows | 8080 |
| Custom PostgreSQL | Temporal persistence layer | 5432 |
| Database Init Job | Database setup and initialization | - |
| Temporal Worker | Sample workflow worker | - |

### Deploying Temporal

#### Deploy with Custom PostgreSQL

```bash
# 1. Deploy custom PostgreSQL instance
kubectl apply -f k8s/demo-app/temporal-postgres.yaml

# 2. Initialize databases
kubectl apply -f k8s/demo-app/temporal-db-init.yaml

# 3. Wait for database initialization to complete
kubectl wait --for=condition=complete job/temporal-db-init -n temporal --timeout=300s

# 4. Deploy Temporal using Helm chart via ArgoCD
kubectl apply -f k8s/demo-app/temporal-application.yaml

# 5. Deploy sample workflow application
kubectl apply -f k8s/demo-app/temporal-workflow-app.yaml

# 6. Verify deployment
kubectl get pods -n temporal
kubectl get pods -n default -l app=temporal-worker
```

#### Manual Deployment Steps

```bash
# Create temporal namespace
kubectl create namespace temporal

# Deploy PostgreSQL
kubectl apply -f k8s/demo-app/temporal-postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n temporal

# Initialize databases
kubectl apply -f k8s/demo-app/temporal-db-init.yaml
kubectl wait --for=condition=complete job/temporal-db-init -n temporal --timeout=300s

# Deploy Temporal server
kubectl apply -f k8s/demo-app/temporal-application.yaml

# Deploy workflow applications
kubectl apply -f k8s/demo-app/temporal-workflow-app.yaml
```

### Accessing Temporal Services

#### Temporal Web UI

```bash
# Port-forward Temporal Web UI
kubectl port-forward svc/temporal-web -n temporal 8080:8080
```

Access Temporal Web UI at: http://localhost:8080

#### Temporal Server (gRPC)

```bash
# Port-forward Temporal Server
kubectl port-forward svc/temporal-frontend -n temporal 7233:7233
```

Connect to Temporal Server at: `localhost:7233`

### Sample Workflow Application

The included sample demonstrates:

- **Workflow Definition**: [`SampleWorkflow`](k8s/demo-app/temporal-workflow-app.yaml:47) with two activities
- **Activities**: `say_hello` and `process_data` with timeout configurations
- **Worker**: Processes workflows from the `sample-task-queue`
- **Starter**: Automatically starts workflows every 30 seconds

#### Workflow Components

```python
@workflow.defn
class SampleWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        # Execute activities with timeouts
        greeting = await workflow.execute_activity(
            say_hello, name, start_to_close_timeout=timedelta(seconds=10)
        )
        processed = await workflow.execute_activity(
            process_data, f"data for {name}", start_to_close_timeout=timedelta(seconds=30)
        )
        return f"{greeting} {processed}"
```

### Monitoring Workflows

#### View Workflow Executions

1. Access Temporal Web UI at http://localhost:8080
2. Navigate to **Workflows** to see running and completed executions
3. Click on any workflow to see detailed execution history

#### Check Worker Logs

```bash
# View worker logs
kubectl logs -l app=temporal-worker -n default

# View workflow starter logs
kubectl logs -l app=workflow-starter -n default
```

### Integrating with Your Application

#### Connect to Temporal from Your App

Update your application deployment to connect to Temporal:

```yaml
env:
  - name: TEMPORAL_HOST
    value: "temporal-frontend.temporal:7233"
  - name: TEMPORAL_NAMESPACE
    value: "default"
```

#### Python Client Example

```python
from temporalio.client import Client

async def main():
    client = await Client.connect("temporal-frontend.temporal:7233")
    
    # Start a workflow
    handle = await client.start_workflow(
        "YourWorkflow",
        "input-data",
        id="unique-workflow-id",
        task_queue="your-task-queue",
    )
    
    # Get result
    result = await handle.result()
    print(f"Workflow result: {result}")
```

### Temporal Observability Integration

Temporal is fully integrated with your existing LGTM observability stack:

#### Metrics Integration

Temporal metrics are automatically exposed and integrated with your existing Prometheus:

```yaml
# Temporal metrics are exposed on port 9090 and can be scraped by your existing Prometheus
# Add this scrape config to your Prometheus configuration:
- job_name: 'temporal-server'
  static_configs:
    - targets: ['temporal-frontend.temporal:9090']
  scrape_interval: 15s
  metrics_path: /metrics

# Key Temporal metrics to monitor:
# - temporal_request_latency_bucket (request latency histograms)
# - temporal_request_count (total requests)
# - temporal_workflow_task_queue_depth (task queue depth)
# - temporal_activity_task_queue_depth (activity queue depth)
```

#### Tracing Integration

Temporal and the sample applications automatically send traces to your existing Tempo instance:

```yaml
# All components send OpenTelemetry traces to:
# Endpoint: http://lgtm.observibility:4317

# Service Names:
# - temporal-server (Temporal server internal operations)
# - temporal-worker (Workflow and activity execution)
# - temporal-workflow-starter (Workflow initiation)

# Traces include:
# - Complete workflow execution lifecycle
# - Individual activity execution with input/output
# - Workflow start and completion events
# - Activity retry attempts and failures
# - Internal Temporal service calls
# - Database operations
# - Custom business logic spans
```

#### Enhanced Tracing Features

The sample applications include comprehensive tracing:

**Workflow Starter Traces:**
- `workflow_execution_cycle` - Complete workflow lifecycle
- `start_workflow` - Workflow initiation with metadata
- `await_workflow_result` - Result waiting and retrieval

**Worker Activity Traces:**
- `say_hello_activity` - Greeting activity with input/output
- `process_data_activity` - Data processing with duration metrics

**Trace Attributes:**
- `workflow.id` - Unique workflow identifier
- `workflow.type` - Workflow class name
- `workflow.status` - Execution status (completed/failed)
- `activity.input` - Activity input parameters
- `activity.output` - Activity return values
- `processing.duration_seconds` - Processing time
- `error.message` - Error details for failed executions

#### Viewing Temporal Traces in Grafana

1. Access Grafana at http://localhost:3000
2. Navigate to **Explore** → **Tempo**
3. Search for traces with:
   - Service name: `temporal-server`
   - Operation: `workflow.execute` or `activity.execute`
4. View detailed workflow execution traces showing:
   - Workflow start and completion
   - Activity executions and retries
   - Task queue operations
   - Database interactions

#### Logs Integration

Temporal logs are automatically collected by Promtail and sent to Loki:

```bash
# View Temporal server logs in Grafana
# Navigate to Explore → Loki
# Query: {namespace="temporal", app="temporal"}

# Or via kubectl:
kubectl logs -l app.kubernetes.io/name=temporal -n temporal
```

The configuration disables Temporal's built-in Prometheus to avoid conflicts with your existing observability stack.

### Troubleshooting Temporal

#### Temporal Server Not Starting

```bash
# Check Temporal server logs
kubectl logs -l app.kubernetes.io/name=temporal -n temporal

# Check PostgreSQL connectivity
kubectl exec -it deployment/temporal-postgresql -n temporal -- psql -U temporal -d temporal -c '\l'
```

#### Workflows Not Executing

```bash
# Check worker registration
kubectl logs -l app=temporal-worker -n default

# Verify task queue in Temporal Web UI
# Navigate to Task Queues section
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
kubectl get pods -n temporal -l app.kubernetes.io/name=postgresql

# Test database connection
kubectl exec -it deployment/temporal-postgresql -n temporal -- \
  psql -U temporal -d temporal -c 'SELECT version();'
```

## Cleanup

```bash
# Delete applications from ArgoCD
kubectl delete -f k8s/argocd/bootstrap/application.yaml

# Delete Temporal resources
kubectl delete -f k8s/demo-app/temporal-application.yaml
kubectl delete -f k8s/demo-app/temporal-workflow-app.yaml
kubectl delete namespace temporal

# Delete all other resources
kubectl delete namespace observibility
kubectl delete deployment demo-app
kubectl delete service demo-app

# Uninstall ArgoCD
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl delete namespace argocd
```