# WP-0067 — Audit Logging & Security Documentation

- Goal: Enable security monitoring and provide production deployment guidance. Log all security-relevant events for incident response. Document complete security setup for production use.
- Idea-ID: IDEA-0003-vibeforge-is-pivoting
- Tasks: TASK-049, TASK-050
- Dependencies: WP-0064, WP-0065, WP-0066 (all security features)

## Task queue (ordered)
1. TASK-049 — Add audit logging for security events
2. TASK-050 — Add security documentation and best practices guide

## Execution plan
1. Add audit logger with JSON lines + rotation and wire into auth, agent lifecycle, dispatch, rate limit, and path validation.
2. Add SECURITY.md with security setup, threat model, and best practices.
3. Link SECURITY.md from CONTROL_PANEL_GUIDE.md and README.md.

## Done means
- `Get-ChildItem logs/audit.log` → exists
- `Get-Content logs/audit.log | ConvertFrom-Json` → valid JSON lines
- `Get-Content docs/SECURITY.md` → comprehensive security guide exists
- Manual: Trigger auth failure → logged
- Manual: Trigger rate limit → logged

## Task checklist
- [x] TASK-049 — Add audit logging for security events
  - Files: apps/api/vibeforge_api/core/audit_logger.py, apps/api/vibeforge_api/core/connection_manager.py, apps/api/vibeforge_api/routers/agent_bridge.py, apps/api/vibeforge_api/routers/control.py, apps/api/vibeforge_api/middleware/rate_limiter.py, tools/agent_bridge/cli_wrapper.py
  - Verify: `python -c "import sys; sys.path.append('apps/api'); from vibeforge_api.core.audit_logger import log_audit_event; log_audit_event('manual_audit_test')"`
  - Verify: `Get-Content logs/audit.log | ConvertFrom-Json`
- [x] TASK-050 — Add security documentation and best practices guide
  - Files: docs/SECURITY.md, docs/CONTROL_PANEL_GUIDE.md, README.md

## Notes / Decisions
- 
