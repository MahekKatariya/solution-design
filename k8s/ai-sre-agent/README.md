# AI SRE Agent

An intelligent system that performs automated root cause analysis by querying the observability stack (LGTM) and correlating data from multiple sources to identify and diagnose system failures.

## Overview

The AI SRE Agent integrates with your LGTM (Loki, Grafana, Tempo, Prometheus) observability stack to:

- **Detect incidents** through alert aggregation and anomaly detection
- **Collect evidence** from metrics, logs, and traces
- **Analyze root causes** using pattern recognition and correlation
- **Generate RCA reports** with structured findings and recommendations
- **Inject failures** for chaos engineering demonstrations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI SRE Agent                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Chaos         │  │   Data          │  │   Analysis   │ │
│  │   Engineering   │  │   Collector     │  │   Engine     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│           │                     │                   │       │
│           └─────────────────────┼───────────────────┘       │
│                                 │                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   RCA Report    │  │   REST API      │                  │
│  │   Generator     │  │   (FastAPI)     │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                Observability Stack (LGTM)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Prometheus  │  │    Loki     │  │   Tempo     │         │
│  │ (Metrics)   │  │   (Logs)    │  │  (Traces)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. FastAPI Application (`app/main.py`)

The main application providing REST API endpoints for:

- **Chaos injection**: Inject failures (pod kill, latency, CPU/memory stress)
- **RCA analysis**: Perform root cause analysis for incidents
- **Observability queries**: Direct access to Prometheus, Loki, and Tempo

### 2. Chaos Engineering Scripts (`scripts/chaos_demo.py`)

Demonstration script that:

- Injects various failure scenarios
- Triggers automated RCA
- Generates comprehensive demo reports

### 3. RCA Report Generator (`scripts/rca_report_generator.py`)

Generates structured RCA reports in:

- JSON format for programmatic consumption
- Markdown format for human readability

## API Endpoints

### Health Check
```
GET /health
```

### Inject Chaos
```
POST /api/v1/chaos/inject
Content-Type: application/json

{
  "failure_type": "kill_pod",  // kill_pod, inject_latency, cpu_stress, memory_stress
  "target_deployment": "temporal-worker",
  "namespace": "default",
  "duration_seconds": 300,
  "intensity": 0.5
}
```

### Perform RCA Analysis
```
POST /api/v1/rca/analyze
Content-Type: application/json

{
  "incident_type": "pod_crash",  // pod_crash, high_latency, memory_pressure, cpu_throttling
  "service_name": "temporal-worker",
  "namespace": "default",
  "severity": "high"
}
```

### Query Observability
```
GET /api/v1/metrics/query?query=up&time_range=3600
GET /api/v1/logs/query?query={app="temporal-worker"}&time_range=3600
GET /api/v1/traces/query?service=temporal-worker&time_range=3600
```

### Run Full Demo
```
POST /api/v1/chaos/demo
```

## Deployment

### Prerequisites

1. Kubernetes cluster with LGTM stack deployed
2. kubectl configured with cluster access
3. Docker for building images

### Build and Deploy

```bash
# Build the Docker image
cd k8s/ai-sre-agent/app
docker build -t ai-sre-agent:latest .

# Push to your registry
docker tag ai-sre-agent:latest your-registry/ai-sre-agent:latest
docker push your-registry/ai-sre-agent:latest

# Deploy to Kubernetes
kubectl apply -f k8s/ai-sre-agent/ai-sre-agent-deployment.yaml
```

### Deploy with ArgoCD

```bash
kubectl apply -f k8s/ai-sre-agent/ai-sre-agent-application.yaml
```

## Usage Examples

### Running a Chaos Demo

```bash
# Run the full demo script
python scripts/chaos_demo.py --agent-url http://localhost:8080 --scenario all

# Run specific scenario
python scripts/chaos_demo.py --scenario pod-kill --output rca_report.json
```

### Manual RCA Analysis

```bash
# Inject a pod kill
curl -X POST http://localhost:8080/api/v1/chaos/inject \
  -H "Content-Type: application/json" \
  -d '{
    "failure_type": "kill_pod",
    "target_deployment": "temporal-worker",
    "namespace": "default"
  }'

# Wait for incident to propagate (30 seconds)

# Perform RCA
curl -X POST http://localhost:8080/api/v1/rca/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "incident_type": "pod_crash",
    "service_name": "temporal-worker",
    "namespace": "default",
    "severity": "high"
  }'
```

### Generating RCA Reports

```python
from rca_report_generator import RCAReportGenerator

generator = RCAReportGenerator()

report = generator.generate_report(
    incident_data={...},
    analysis_results={...},
    evidence_data={...}
)

# Output as JSON
print(generator.to_json(report))

# Output as Markdown
print(generator.to_markdown(report))
```

### Generate rca report

```bash
python scripts/rca_report_generator.py --incident-id INC-001
```

## RCA Report Structure

Each RCA report includes:

1. **Executive Summary**: High-level incident overview
2. **Timeline**: Chronological sequence of events
3. **Root Cause Analysis**: Identified root cause with confidence score
4. **Impact Assessment**: Affected services, users, and duration
5. **Recommendations**: Prioritized remediation actions
6. **Lessons Learned**: Key takeaways from the incident
7. **Evidence**: Supporting metrics, logs, and traces

## Supported Failure Scenarios

| Scenario | Description | Detection Method |
|----------|-------------|------------------|
| Pod Kill | Terminates a pod unexpectedly | Kubernetes events, restart counts |
| High Latency | Injects network latency | Prometheus latency metrics |
| CPU Stress | Consumes excessive CPU | CPU throttling metrics |
| Memory Stress | Consumes excessive memory | OOMKilled events, memory metrics |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_URL` | `http://lgtm.observibility:9090` | Prometheus endpoint |
| `LOKI_URL` | `http://lgtm.observibility:3100` | Loki endpoint |
| `TEMPO_URL` | `http://lgtm.observibility:3200` | Tempo endpoint |
| `GRAFANA_URL` | `http://lgtm.observibility:3000` | Grafana endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## RBAC Requirements

The AI SRE Agent requires the following Kubernetes permissions:

- Read/write access to pods, deployments, events
- Exec access to pods (for stress injection)
- Access to metrics.k8s.io for resource metrics

See `ai-sre-agent-deployment.yaml` for complete RBAC configuration.

## Future Enhancements

- [ ] Integration with LLM for enhanced analysis
- [ ] Automated remediation actions
- [ ] Slack/Teams notifications
- [ ] Historical incident database
- [ ] ML-based anomaly detection
- [ ] Integration with incident management tools (PagerDuty, ServiceNow)

## License

MIT License
