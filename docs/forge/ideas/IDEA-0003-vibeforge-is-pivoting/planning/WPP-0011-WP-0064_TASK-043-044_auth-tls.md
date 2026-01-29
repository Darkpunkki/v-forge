# WP-0064 — Authentication & TLS Foundation

- Goal: Establish foundational security with real authentication and encrypted connections. Replace hardcoded credentials with secure token validation. Enable HTTPS/WSS for encrypted communication between UI, API, and agents.
- Idea-ID: IDEA-0003-vibeforge-is-pivoting
- Tasks: TASK-043, TASK-044
- Dependencies: MVP complete (WP-0060)

## Task queue (ordered)
1. TASK-043 — Replace hardcoded 'secret' token with secure authentication system
2. TASK-044 — Add TLS/SSL support with self-signed certificates for testing

## Execution plan
1. Implement server-side auth token generation + validation middleware for REST + WebSocket endpoints.
2. Update agent bridge token handling verification and documentation.
3. Add TLS certificate generation script and document HTTPS/WSS usage.
4. Extend agent bridge to support WSS and optional insecure mode for self-signed certs.

## Done means
- `cd apps/api && python -m pytest tests/test_auth.py -v`
- `cd apps/api && python -m pytest`
- `powershell -File tools/generate_certs.ps1`
- `uvicorn vibeforge_api.main:app --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem`
- `python tools/agent_bridge/bridge.py --url wss://localhost:8000/ws/agent-bridge --token <generated> --workdir . --insecure`

## Task checklist
- [x] TASK-043 — Replace hardcoded 'secret' token with secure authentication system
  - Files: apps/api/vibeforge_api/core/auth.py, apps/api/vibeforge_api/routers/control.py, apps/api/vibeforge_api/routers/agent_bridge.py, apps/api/tests/test_auth.py, apps/api/tests/conftest.py, apps/ui/src/api/controlClient.ts, docs/CONTROL_PANEL_GUIDE.md
  - Verify: `cd apps/api && python -m pytest tests/test_auth.py -v`
- [x] TASK-044 — Add TLS/SSL support with self-signed certificates for testing
  - Files: tools/generate_certs.ps1, tools/agent_bridge/bridge.py (WSS support already implemented), docs/CONTROL_PANEL_GUIDE.md
  - Verify: `powershell -File tools/generate_certs.ps1` (generates ssl/cert.pem + ssl/key.pem)
  - Verify: `uvicorn vibeforge_api.main:app --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem` (API starts with TLS)
  - Verify: `python tools/agent_bridge/bridge.py --url wss://localhost:8000/ws/agent-bridge --agent-id test --token <token> --workdir . --insecure` (WSS connection works)

## Notes / Decisions
- `tools/generate_certs.ps1` expects PowerShell; `python tools/generate_certs.ps1` will fail with syntax error.
- Ran powershell -File tools/generate_certs.ps1 (Git openssl fallback); generated ssl/cert.pem + ssl/key.pem with a non-fatal openssl signal pipe warning.
