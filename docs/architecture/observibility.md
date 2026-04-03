# Observability Architecture

## Goals

- Full visibility into system health
- Fast incident detection
- Root cause analysis

---

## Stack

| Type | Tool |
|------|------|
| Metrics | Prometheus |
| Logs | Loki |
| Tracing | Jaeger |
| Dashboards | Grafana |

---

## Metrics

Golden Signals:
- Latency
- Traffic
- Errors
- Saturation

---

## Logging

- Structured JSON logs
- Correlation ID per request
- Centralized via Loki

---

## Tracing

- OpenTelemetry instrumentation
- Distributed tracing across services

---

## Alerting

- Critical → PagerDuty
- Warning → Slack

Examples:
- High error rate (>5%)
- Pod crash loops
- DB latency spike