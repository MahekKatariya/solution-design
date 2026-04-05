#!/usr/bin/env python3
"""
RCA Report Generator
Generates structured Root Cause Analysis reports from incident data
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import textwrap


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class TimelineEvent:
    """Represents a single event in the incident timeline"""
    timestamp: str
    event_type: str
    description: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    """Represents evidence collected during RCA"""
    evidence_type: str  # metric, log, trace, event
    timestamp: str
    source: str
    content: str
    relevance: str  # high, medium, low
    tags: List[str] = field(default_factory=list)


@dataclass
class RootCause:
    """Represents the identified root cause"""
    category: str  # infrastructure, application, network, configuration, external
    description: str
    confidence: float  # 0.0 to 1.0
    contributing_factors: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Recommendation:
    """Represents a remediation recommendation"""
    priority: int  # 1 = highest
    category: str  # immediate, short_term, long_term, preventive
    action: str
    rationale: str
    estimated_effort: str  # low, medium, high
    automation_possible: bool


@dataclass
class ImpactAssessment:
    """Represents the impact of the incident"""
    affected_services: List[str]
    affected_users: str  # estimated number or percentage
    duration_minutes: int
    data_loss: bool
    revenue_impact: Optional[str] = None
    reputation_impact: Optional[str] = None


@dataclass
class RCAReport:
    """Complete RCA Report structure"""
    report_id: str
    incident_id: str
    generated_at: str
    incident_summary: str
    severity: str
    status: str
    timeline: List[TimelineEvent]
    evidence: List[Evidence]
    root_cause: RootCause
    impact: ImpactAssessment
    recommendations: List[Recommendation]
    lessons_learned: List[str]
    appendices: Dict[str, Any] = field(default_factory=dict)


class RCAReportGenerator:
    """Generates structured RCA reports"""
    
    def __init__(self):
        self.report_counter = 0
    
    def generate_report(
        self,
        incident_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        evidence_data: Dict[str, Any]
    ) -> RCAReport:
        """Generate a complete RCA report from incident and analysis data"""
        
        self.report_counter += 1
        report_id = f"RCA-{datetime.now().strftime('%Y%m%d')}-{self.report_counter:04d}"
        
        # Build timeline
        timeline = self._build_timeline(incident_data, analysis_results)
        
        # Build evidence
        evidence = self._build_evidence(evidence_data)
        
        # Determine root cause
        root_cause = self._determine_root_cause(analysis_results, evidence)
        
        # Assess impact
        impact = self._assess_impact(incident_data, analysis_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(root_cause, analysis_results)
        
        # Extract lessons learned
        lessons = self._extract_lessons_learned(root_cause, analysis_results)
        
        return RCAReport(
            report_id=report_id,
            incident_id=incident_data.get("incident_id", "unknown"),
            generated_at=datetime.now().isoformat(),
            incident_summary=self._generate_summary(incident_data, root_cause),
            severity=incident_data.get("severity", "medium"),
            status=self._determine_status(incident_data),
            timeline=timeline,
            evidence=evidence,
            root_cause=root_cause,
            impact=impact,
            recommendations=recommendations,
            lessons_learned=lessons,
            appendices={
                "raw_metrics": evidence_data.get("metrics", [])[:10],
                "raw_logs": evidence_data.get("logs", [])[:10],
                "configuration": incident_data.get("configuration", {})
            }
        )
    
    def _build_timeline(
        self,
        incident_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> List[TimelineEvent]:
        """Build incident timeline"""
        timeline = []
        
        # Add detection event
        if "detection_time" in incident_data:
            timeline.append(TimelineEvent(
                timestamp=incident_data["detection_time"],
                event_type="detection",
                description="Incident detected by monitoring system",
                source="Prometheus AlertManager",
                metadata={"alert_name": incident_data.get("alert_name", "unknown")}
            ))
        
        # Add key findings as timeline events
        for finding in analysis_results.get("key_findings", []):
            timeline.append(TimelineEvent(
                timestamp=finding.get("timestamp", datetime.now().isoformat()),
                event_type="finding",
                description=finding.get("finding", "Unknown finding"),
                source=finding.get("source", "analysis"),
                metadata={"finding_type": finding.get("type", "general")}
            ))
        
        # Add remediation events
        for action in analysis_results.get("actions_taken", []):
            timeline.append(TimelineEvent(
                timestamp=action.get("timestamp", datetime.now().isoformat()),
                event_type="remediation",
                description=action.get("description", "Remediation action taken"),
                source="automated" if action.get("automated") else "manual",
                metadata={"action_id": action.get("id", "unknown")}
            ))
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.timestamp)
        
        return timeline
    
    def _build_evidence(self, evidence_data: Dict[str, Any]) -> List[Evidence]:
        """Build evidence list from collected data"""
        evidence = []
        
        # Process metrics
        for metric in evidence_data.get("metrics", [])[:20]:
            evidence.append(Evidence(
                evidence_type="metric",
                timestamp=metric.get("timestamp", datetime.now().isoformat()),
                source="Prometheus",
                content=f"{metric.get('name', 'unknown')}: {metric.get('value', 'N/A')}",
                relevance="high" if metric.get("anomaly") else "medium",
                tags=metric.get("labels", [])
            ))
        
        # Process logs
        for log in evidence_data.get("logs", [])[:20]:
            evidence.append(Evidence(
                evidence_type="log",
                timestamp=log.get("timestamp", datetime.now().isoformat()),
                source=log.get("source", "Loki"),
                content=log.get("message", "")[:500],
                relevance="high" if "error" in log.get("message", "").lower() else "medium",
                tags=log.get("labels", [])
            ))
        
        # Process traces
        for trace in evidence_data.get("traces", [])[:10]:
            evidence.append(Evidence(
                evidence_type="trace",
                timestamp=trace.get("timestamp", datetime.now().isoformat()),
                source="Tempo",
                content=f"Trace {trace.get('trace_id', 'unknown')}: {trace.get('operation', 'unknown')} ({trace.get('duration_ms', 0)}ms)",
                relevance="high" if trace.get("status") == "ERROR" else "medium",
                tags=["distributed-tracing"]
            ))
        
        return evidence
    
    def _determine_root_cause(
        self,
        analysis_results: Dict[str, Any],
        evidence: List[Evidence]
    ) -> RootCause:
        """Determine the root cause from analysis results"""
        
        incident_type = analysis_results.get("incident_type", "unknown")
        
        # Predefined root cause patterns
        root_cause_patterns = {
            "pod_crash": {
                "category": "infrastructure",
                "description": "Pod crashed due to resource constraints or application error",
                "confidence": 0.85,
                "contributing_factors": [
                    "Memory limit exceeded",
                    "Application panic/fatal error",
                    "Liveness probe failure"
                ]
            },
            "high_latency": {
                "category": "application",
                "description": "Increased latency due to resource contention or inefficient code path",
                "confidence": 0.75,
                "contributing_factors": [
                    "Database query slowdown",
                    "Network latency",
                    "Resource throttling"
                ]
            },
            "memory_pressure": {
                "category": "infrastructure",
                "description": "Memory pressure leading to OOM kills or performance degradation",
                "confidence": 0.90,
                "contributing_factors": [
                    "Memory leak in application",
                    "Insufficient memory allocation",
                    "Unexpected traffic spike"
                ]
            },
            "cpu_throttling": {
                "category": "infrastructure",
                "description": "CPU throttling due to insufficient CPU resources",
                "confidence": 0.85,
                "contributing_factors": [
                    "CPU limit too low",
                    "Inefficient algorithms",
                    "Unexpected compute load"
                ]
            }
        }
        
        pattern = root_cause_patterns.get(incident_type, {
            "category": "unknown",
            "description": "Root cause requires further investigation",
            "confidence": 0.50,
            "contributing_factors": []
        })
        
        # Adjust confidence based on evidence
        high_relevance_count = sum(1 for e in evidence if e.relevance == "high")
        confidence_adjustment = min(0.1, high_relevance_count * 0.02)
        
        return RootCause(
            category=pattern["category"],
            description=pattern["description"],
            confidence=min(1.0, pattern["confidence"] + confidence_adjustment),
            contributing_factors=pattern["contributing_factors"],
            evidence_ids=[f"evidence-{i}" for i in range(min(5, len(evidence)))]
        )
    
    def _assess_impact(
        self,
        incident_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> ImpactAssessment:
        """Assess the impact of the incident"""
        
        return ImpactAssessment(
            affected_services=analysis_results.get("affected_services", ["unknown"]),
            affected_users=incident_data.get("affected_users", "unknown"),
            duration_minutes=incident_data.get("duration_minutes", 0),
            data_loss=analysis_results.get("data_loss", False),
            revenue_impact=incident_data.get("revenue_impact"),
            reputation_impact=incident_data.get("reputation_impact")
        )
    
    def _generate_recommendations(
        self,
        root_cause: RootCause,
        analysis_results: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate remediation recommendations"""
        
        recommendations = []
        
        if root_cause.category == "infrastructure":
            recommendations.extend([
                Recommendation(
                    priority=1,
                    category="immediate",
                    action="Increase resource limits for affected containers",
                    rationale="Current limits are insufficient for the workload",
                    estimated_effort="low",
                    automation_possible=True
                ),
                Recommendation(
                    priority=2,
                    category="short_term",
                    action="Implement Vertical Pod Autoscaler (VPA)",
                    rationale="Enable automatic resource adjustment based on usage",
                    estimated_effort="medium",
                    automation_possible=True
                ),
                Recommendation(
                    priority=3,
                    category="long_term",
                    action="Conduct capacity planning review",
                    rationale="Ensure cluster resources match workload requirements",
                    estimated_effort="high",
                    automation_possible=False
                )
            ])
        
        elif root_cause.category == "application":
            recommendations.extend([
                Recommendation(
                    priority=1,
                    category="immediate",
                    action="Review and optimize slow code paths",
                    rationale="Identified performance bottlenecks in application",
                    estimated_effort="medium",
                    automation_possible=False
                ),
                Recommendation(
                    priority=2,
                    category="short_term",
                    action="Implement caching for frequently accessed data",
                    rationale="Reduce database load and improve response times",
                    estimated_effort="medium",
                    automation_possible=False
                ),
                Recommendation(
                    priority=3,
                    category="preventive",
                    action="Add performance testing to CI/CD pipeline",
                    rationale="Catch performance regressions before production",
                    estimated_effort="medium",
                    automation_possible=True
                )
            ])
        
        # Add generic preventive recommendations
        recommendations.extend([
            Recommendation(
                priority=4,
                category="preventive",
                action="Enhance monitoring and alerting for early detection",
                rationale="Improve mean time to detection (MTTD)",
                estimated_effort="low",
                automation_possible=True
            ),
            Recommendation(
                priority=5,
                category="preventive",
                action="Document incident in knowledge base",
                rationale="Enable faster resolution of similar future incidents",
                estimated_effort="low",
                automation_possible=False
            )
        ])
        
        return recommendations
    
    def _extract_lessons_learned(
        self,
        root_cause: RootCause,
        analysis_results: Dict[str, Any]
    ) -> List[str]:
        """Extract lessons learned from the incident"""
        
        lessons = []
        
        if root_cause.confidence >= 0.8:
            lessons.append("Root cause was identified with high confidence, demonstrating effective observability coverage")
        else:
            lessons.append("Root cause identification had lower confidence, consider enhancing monitoring coverage")
        
        if analysis_results.get("detection_time_minutes", 0) > 5:
            lessons.append("Detection time exceeded 5 minutes, review alert thresholds and rules")
        
        if analysis_results.get("manual_intervention_required", False):
            lessons.append("Manual intervention was required, consider automation opportunities")
        
        lessons.append("Regular chaos engineering exercises help validate system resilience")
        
        return lessons
    
    def _generate_summary(
        self,
        incident_data: Dict[str, Any],
        root_cause: RootCause
    ) -> str:
        """Generate incident summary"""
        
        return f"Incident {incident_data.get('incident_id', 'unknown')}: {root_cause.category} issue causing {incident_data.get('incident_type', 'service disruption')}. Root cause: {root_cause.description}"
    
    def _determine_status(self, incident_data: Dict[str, Any]) -> str:
        """Determine current incident status"""
        
        if incident_data.get("resolved", False):
            return IncidentStatus.RESOLVED.value
        elif incident_data.get("root_cause_identified", False):
            return IncidentStatus.IDENTIFIED.value
        else:
            return IncidentStatus.INVESTIGATING.value
    
    def to_json(self, report: RCAReport) -> str:
        """Convert report to JSON string"""
        return json.dumps(asdict(report), indent=2, default=str)
    
    def to_markdown(self, report: RCAReport) -> str:
        """Convert report to Markdown format"""
        
        md = f"""# Root Cause Analysis Report

## Report Information
- **Report ID:** {report.report_id}
- **Incident ID:** {report.incident_id}
- **Generated At:** {report.generated_at}
- **Severity:** {report.severity.upper()}
- **Status:** {report.status.upper()}

## Executive Summary

{report.incident_summary}

## Timeline

"""
        
        for event in report.timeline:
            md += f"- **{event.timestamp}** [{event.event_type.upper()}]: {event.description}\n"
        
        md += f"""
## Root Cause Analysis

### Primary Root Cause
**Category:** {report.root_cause.category}

**Description:** {report.root_cause.description}

**Confidence:** {report.root_cause.confidence * 100:.0f}%

### Contributing Factors
"""
        for factor in report.root_cause.contributing_factors:
            md += f"- {factor}\n"
        
        md += f"""
## Impact Assessment

- **Affected Services:** {', '.join(report.impact.affected_services)}
- **Affected Users:** {report.impact.affected_users}
- **Duration:** {report.impact.duration_minutes} minutes
- **Data Loss:** {'Yes' if report.impact.data_loss else 'No'}
"""
        
        if report.impact.revenue_impact:
            md += f"- **Revenue Impact:** {report.impact.revenue_impact}\n"
        
        md += """
## Recommendations

"""
        for rec in report.recommendations:
            md += f"""### {rec.priority}. {rec.action}
- **Category:** {rec.category}
- **Rationale:** {rec.rationale}
- **Effort:** {rec.estimated_effort}
- **Automation Possible:** {'Yes' if rec.automation_possible else 'No'}

"""
        
        md += """## Lessons Learned

"""
        for lesson in report.lessons_learned:
            md += f"- {lesson}\n"
        
        md += """
## Evidence Summary

"""
        md += f"- Total evidence items: {len(report.evidence)}\n"
        md += f"- High relevance: {sum(1 for e in report.evidence if e.relevance == 'high')}\n"
        md += f"- Medium relevance: {sum(1 for e in report.evidence if e.relevance == 'medium')}\n"
        md += f"- Low relevance: {sum(1 for e in report.evidence if e.relevance == 'low')}\n"
        
        md += """
---

*This report was generated automatically by the AI SRE Agent.*
"""
        
        return md


# Example usage
if __name__ == "__main__":
    # Sample incident data
    incident_data = {
        "incident_id": "INC-2024-001",
        "incident_type": "pod_crash",
        "severity": "high",
        "detection_time": "2024-01-15T10:30:00Z",
        "duration_minutes": 45,
        "affected_users": "~1000 users",
        "resolved": True,
        "root_cause_identified": True
    }
    
    # Sample analysis results
    analysis_results = {
        "incident_type": "pod_crash",
        "key_findings": [
            {
                "timestamp": "2024-01-15T10:30:15Z",
                "finding": "Pod temporal-worker-abc123 terminated with OOMKilled",
                "source": "Kubernetes Events",
                "type": "error"
            },
            {
                "timestamp": "2024-01-15T10:31:00Z",
                "finding": "Memory usage exceeded 512Mi limit",
                "source": "Prometheus Metrics",
                "type": "metric_anomaly"
            }
        ],
        "affected_services": ["temporal-worker", "temporal-server"],
        "actions_taken": [
            {
                "timestamp": "2024-01-15T10:35:00Z",
                "description": "Increased memory limit to 1Gi",
                "automated": True,
                "id": "action-001"
            }
        ],
        "data_loss": False
    }
    
    # Sample evidence data
    evidence_data = {
        "metrics": [
            {"name": "container_memory_usage", "value": "536870912", "timestamp": "2024-01-15T10:29:00Z", "anomaly": True},
            {"name": "container_cpu_usage", "value": "0.5", "timestamp": "2024-01-15T10:29:00Z", "anomaly": False}
        ],
        "logs": [
            {"message": "OOMKilled - Container exceeded memory limit", "timestamp": "2024-01-15T10:30:00Z", "source": "kubelet"},
            {"message": "Memory allocation failed", "timestamp": "2024-01-15T10:29:55Z", "source": "application"}
        ],
        "traces": [
            {"trace_id": "abc123", "operation": "process_workflow", "duration_ms": 5000, "status": "ERROR", "timestamp": "2024-01-15T10:29:50Z"}
        ]
    }
    
    # Generate report
    generator = RCAReportGenerator()
    report = generator.generate_report(incident_data, analysis_results, evidence_data)
    
    # Output JSON
    print("=" * 80)
    print("JSON OUTPUT")
    print("=" * 80)
    print(generator.to_json(report))
    
    # Output Markdown
    print("\n" + "=" * 80)
    print("MARKDOWN OUTPUT")
    print("=" * 80)
    print(generator.to_markdown(report))
