---
phase: monitoring
title: Monitoring & Observability
description: Define monitoring strategy, metrics, alerts, and incident response
---

# Monitoring & Observability

## Key Metrics
**What do we need to track?**

### Performance Metrics
- API latency and throughput for `/sessions` endpoints (question fetch, answer submit, plan summary).
- Workspace I/O timings (patch apply duration, workspace creation time).
- Model call latency and failure rate (OpenAI or future providers).

### Business Metrics
- Sessions created per day and completion rate (questionnaire → plan decision).
- Plan approval vs. rejection rates and time-to-approval.
- Workspace generation success rate and artifact count per session.

### Error Metrics
- Phase transition violations and invalid patch attempts.
- HTTP 4xx/5xx by endpoint; exception types from core modules.
- Model provider errors (auth, rate limit, network) and fallback usage.

## Monitoring Tools
**What tools are we using?**

- **APM/logging**: start with FastAPI/uvicorn access logs; plan to add OpenTelemetry exporters when remote.
- **Infrastructure**: OS-level metrics via container provider when deployed; local runs rely on developer observability.
- **Logs**: structured logs for session transitions, workspace creation, and patch application outcomes.
- **User analytics**: capture questionnaire completion stats in future UI telemetry (opt-in).

## Logging Strategy
**What do we log and how?**

- Use structured JSON logs for session/phase changes, patch validation results, and plan decisions.
- Redact secrets and skip logging raw model prompts/responses that contain customer context.
- Retain logs locally per run; centralize to log aggregation when cloud deployment exists.

## Alerts & Notifications
**When and how do we get notified?**

### Critical Alerts
- Patch application failure rate exceeds threshold → block further runs and investigate workspace integrity.
- Model provider authentication failures sustained over N minutes → fail fast and notify operators.

### Warning Alerts
- Elevated 4xx responses on questionnaire endpoints → check UI/client contract changes.
- Increased plan rejection rates → review prompt quality or questionnaire options.

## Dashboards
**What do we visualize?**

- System health: request rate, latency percentiles, error rates per endpoint.
- Business funnel: sessions started → questionnaire completed → plans approved.
- Workspace metrics: patch durations, workspace sizes, artifact counts.

## Incident Response
**How do we handle issues?**

### On-Call Rotation
- Solo project today; when team grows, introduce rotation and escalation tree.

### Incident Process
1. Detection via alerts/log review.
2. Investigate logs for session/patch errors; reproduce against a sandbox workspace.
3. Mitigate by disabling risky flows or rolling back image; communicate status.
4. Post-mortem with root cause, prevention steps, and test coverage additions.

## Health Checks
**How do we verify system health?**

- `/health` endpoint for liveness.
- Smoke tests: create session → fetch question → submit answer → fetch plan summary.
- Periodic patch validation dry-runs to ensure traversal protections are active.
