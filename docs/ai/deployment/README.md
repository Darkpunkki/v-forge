---
phase: deployment
title: Deployment Strategy
description: Define deployment process, infrastructure, and release procedures
---

# Deployment Strategy

## Infrastructure
**Where will the application run?**

- **Local-first**: run FastAPI locally via `uvicorn` with `.venv` for developers; default port 8000.
- **Target cloud (future)**: containerized API on AWS/GCP with persistent volume for `workspaces/` and secrets in a managed store.
- **Environment separation**: local dev only today; plan for staging/prod once remote UI/API is exposed.

## Deployment Pipeline
**How do we deploy changes?**

### Build Process
- API: `pip install -r requirements.txt` then package via Docker (when remote) with `uvicorn vibeforge_api.main:app` entrypoint.
- UI: Vite build to static assets once UI work resumes.
- Environment configuration via `.env` (local) or secret store (cloud); never bake keys into images.

### CI/CD Pipeline
- Current: manual testing via `pytest` from `apps/api` before pushing.
- Next steps: add CI job for unit tests and future linting; publish Docker image on main branch.

## Environment Configuration
**What settings differ per environment?**

### Development
- `.env` in `apps/api` with `OPENAI_API_KEY` and optional feature flags.
- Local file system hosts `workspaces/`; ensure directory is gitignored.

### Staging
- Containerized API with mounted storage for workspaces/artifacts.
- Use staging OpenAI/project keys; enable basic auth or network allowlist.

### Production
- Hardened secrets management (AWS Secrets Manager/GCP Secret Manager).
- Observability stack (APM + logs) and stricter ingress controls; default read-only file system except mounted workspace volume.

## Deployment Steps
**What's the release process?**

1. Run `pytest` in `apps/api` and ensure all tests pass.
2. Build container image (future) with pinned dependency versions.
3. Deploy to target environment (local: `uvicorn ... --reload`; cloud: rolling update of container).
4. Validate `/health` endpoint and smoke test questionnaire/plan endpoints.
5. If issues arise, execute rollback plan.

## Database Migrations
**How do we handle schema changes?**

- No database today; migrations are N/A. Introduce Alembic or Prisma once a DB is added.
- For schema-like changes (JSON structures), version JSON schemas in `/schemas` and bump consumers together.

## Secrets Management
**How do we handle sensitive data?**

- Store `OPENAI_API_KEY` (and future provider keys) in `.env` locally; use secret manager in cloud deployments.
- Never commit secrets; rotate keys when incidents occur.
- Keep API tokens scoped to least privilege and validate before startup.

## Rollback Plan
**What if something goes wrong?**

- Local: stop the server and revert to last known-good commit; delete corrupted session workspace if needed.
- Cloud: rollback container to previous image; invalidate affected workspaces after snapshot/backup.
- Communicate outages in release notes and require smoke-test signoff before re-attempting deploy.
