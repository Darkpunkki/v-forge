# WP-0066 — Rate Limiting & Cost Controls

- Goal: Prevent abuse and runaway costs. Limit dispatch frequency per agent and per IP. Track Claude API costs per session and enforce daily/session limits.
- Idea-ID: IDEA-0003-vibeforge-is-pivoting
- Tasks: TASK-047, TASK-048
- Dependencies: WP-0064 (auth for user tracking)

## Task queue (ordered)
1. TASK-047 — Implement rate limiting for dispatch endpoints
2. TASK-048 — Add cost tracking and limits per session/user

## Execution plan
1. Add rate limiting middleware for dispatch endpoints with per-agent + per-IP limits and headers.
2. Add cost tracking with daily/session limits and update control context response.
3. Add tests for rate limiting and cost limits.

## Done means
- `cd apps/api && python -m pytest tests/test_rate_limiting.py -v`
- `cd apps/api && python -m pytest tests/test_cost_limits.py -v`
- Manual: Send 11 dispatches in 1 minute → 11th returns 429
- Manual: Exceed daily cost limit → dispatch blocked with 402

## Task checklist
- [x] TASK-047 — Implement rate limiting for dispatch endpoints
  - Files: apps/api/vibeforge_api/middleware/rate_limiter.py, apps/api/vibeforge_api/main.py, apps/api/tests/test_rate_limiting.py
  - Verify: `cd apps/api && python -m pytest tests/test_rate_limiting.py -v`
- [x] TASK-048 — Add cost tracking and limits per session/user
  - Files: apps/api/vibeforge_api/core/cost_tracker.py, apps/api/vibeforge_api/core/connection_manager.py, apps/api/vibeforge_api/routers/control.py, apps/api/tests/test_cost_limits.py, apps/ui/src/api/controlClient.ts
  - Verify: `cd apps/api && python -m pytest tests/test_cost_limits.py -v`

## Notes / Decisions
- 
