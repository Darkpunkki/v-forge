# Task Status — IDEA-0003-vibeforge-is-pivoting

**Last Updated:** 2026-01-29
**Status:** MVP Complete, V1 Queued (Security→Features)
**Total Tasks:** 50 (MVP: 36, V1: 12, Later: 2)
**Total WPs:** 14 (MVP: 8 Done, V1: 6 Queued)

## Quick Summary

- ✅ **MVP Complete** (36/36 tasks, 8/8 WPs) — All 6 MVP epics done
- ⏳ **V1 Security Hardening** (0/8 tasks, 0/4 WPs) — Must complete first
- ⏳ **V1 Features** (0/4 tasks, 0/2 WPs) — After security complete
- 📋 **Later Planned** (0/2 tasks) — External control channels + deployment

---

## Epic Status

| Epic | Status | Tasks | Progress | Priority |
|---|---|---|---|---|
| **EPIC-001** — Legacy Session Removal | ✅ Done | 4/4 | 100% | Completed |
| **EPIC-002** — Agent Bridge Protocol | ✅ Done | 9/9 | 100% | Completed |
| **EPIC-003** — Agent Bridge Service | ✅ Done | 5/5 | 100% | Completed |
| **EPIC-004** — Live Agent Control Backend | ✅ Done | 5/5 | 100% | Completed |
| **EPIC-005** — Async Dispatch Engine | ✅ Done | 5/5 | 100% | Completed |
| **EPIC-006** — Live Agent Control UI | ✅ Done | 8/8 | 100% | Completed |
| **EPIC-009** — Security Hardening | ⏳ Queued | 0/8 | 0% | **P0 - Next** |
| **EPIC-007** — Multi-Agent Orchestration | ⏳ Queued | 0/4 | 0% | P1 - After Security |
| **EPIC-008** — External Control Channels | 📋 Later | 0/2 | 0% | P2 |

---

## Work Package Status

| WP | Status | Epic | Tasks | Priority |
|---|---|---|---|---|
| **MVP (Complete)** | | | | |
| WP-0053 | ✅ Done | EPIC-001 | TASK-001, 002, 003, 004 | — |
| WP-0054 | ✅ Done | EPIC-002 | TASK-005, 006, 009, 013 | — |
| WP-0055 | ✅ Done | EPIC-002 | TASK-007, 008, 010, 011, 012 | — |
| WP-0056 | ✅ Done | EPIC-003 | TASK-014, 015, 016, 017, 018 | — |
| WP-0057 | ✅ Done | EPIC-004 | TASK-019, 020, 021, 022, 041 | — |
| WP-0058 | ✅ Done | EPIC-005 | TASK-023, 024, 025, 026, 027 | — |
| WP-0059 | ✅ Done | EPIC-006 | TASK-028, 029, 030, 031, 032, 033 | — |
| WP-0060 | ✅ Done | EPIC-006 | TASK-034, 042 | — |
| **V1 Security (Next Priority)** | | | | |
| WP-0064 | ⏳ Queued | EPIC-009 | TASK-043, 044 | **1st - Start Here** |
| WP-0065 | ⏳ Queued | EPIC-009 | TASK-045, 046 | 2nd |
| WP-0066 | ⏳ Queued | EPIC-009 | TASK-047, 048 | 3rd |
| WP-0067 | ⏳ Queued | EPIC-009 | TASK-049, 050 | 4th |
| **V1 Features (After Security)** | | | | |
| WP-0062 | ⏳ Queued | EPIC-007 | TASK-035, 036 | 5th |
| WP-0063 | ⏳ Queued | EPIC-007 | TASK-037, 038 | 6th |

---

## Task Details (MVP — All Complete)

### EPIC-001 — Legacy Session Removal (4/4) ✅

- ✅ **TASK-001** — Delete legacy session UI screen files
- ✅ **TASK-002** — Delete sessions router and remove from main.py
- ✅ **TASK-003** — Remove session-specific request and response models
- ✅ **TASK-004** — Update App.tsx routes and remove session API client

### EPIC-002 — Agent Bridge Protocol and Connection Manager (9/9) ✅

- ✅ **TASK-005** — Define agent bridge protocol Pydantic models
- ✅ **TASK-006** — Add unit tests for bridge protocol serialization
- ✅ **TASK-007** — Implement WebSocket endpoint at /ws/agent-bridge
- ✅ **TASK-008** — Add heartbeat monitoring and stale connection detection
- ✅ **TASK-009** — Add agent bridge event types to EventLog
- ✅ **TASK-010** — Build RemoteAgentConnectionManager singleton
- ✅ **TASK-011** — Add dispatch and response buffering to connection manager
- ✅ **TASK-012** — Add unit tests for RemoteAgentConnectionManager
- ✅ **TASK-013** — Add agent connection fields to Session model

### EPIC-003 — Agent Bridge Service (5/5) ✅

- ✅ **TASK-014** — Build bridge WebSocket client with registration handshake
- ✅ **TASK-015** — Add heartbeat sending and reconnection with backoff
- ✅ **TASK-016** — Implement Claude Code CLI wrapper for task execution
- ✅ **TASK-017** — Wire dispatch handling to CLI execution with progress streaming
- ✅ **TASK-018** — Add CLI interface and signal handling to bridge

### EPIC-004 — Live Agent Control Backend (5/5) ✅

- ✅ **TASK-019** — Add agent registration and listing endpoints to /control
- ✅ **TASK-020** — Add task dispatch and follow-up endpoints
- ✅ **TASK-021** — Extend SSE streaming with agent-specific event types
- ✅ **TASK-022** — Add integration tests for agent control endpoints
- ✅ **TASK-041** — Replace session list/status endpoints with control context

### EPIC-005 — Async Dispatch Engine (5/5) ✅

- ✅ **TASK-023** — Add agent_type field to AgentConfig model
- ✅ **TASK-024** — Add async dispatch path in TickEngine.advance_tick()
- ✅ **TASK-025** — Add response buffer checking to TickEngine tick loop
- ✅ **TASK-026** — Add dispatch timeout handling
- ✅ **TASK-027** — Add tests for async dispatch and response buffering in TickEngine

### EPIC-006 — Live Agent Control UI (8/8) ✅

- ✅ **TASK-028** — Add agent registration API functions to controlClient.ts
- ✅ **TASK-029** — Build AgentRegistrationPanel React component
- ✅ **TASK-030** — Add task dispatch and follow-up API functions
- ✅ **TASK-031** — Build TaskDispatchPanel chat-style React component
- ✅ **TASK-032** — Build StreamingOutputView React component
- ✅ **TASK-033** — Build AgentConnectionDashboard React component
- ✅ **TASK-034** — Rework ControlPanel.tsx layout for agent-centric experience
- ✅ **TASK-042** — Remove session list/status UI and wire control context

---

## Next Steps (V1 Security Hardening — Priority!)

### EPIC-009 — Security Hardening (0/8) ⏳

**Why Security First:**
- Current MVP has no real authentication (hardcoded "secret")
- No encryption (ws://, http:// unencrypted)
- No input validation (vulnerable to injection)
- No rate limiting (abuse possible)
- Required before delegation chains (increased attack surface)
- Required before external control (cloud/WhatsApp)

#### WP-0064: Authentication & TLS Foundation (4 points)

- ⏳ **TASK-043** — Replace hardcoded 'secret' token with secure authentication
  - Generate secure random tokens (32+ bytes)
  - Token validation middleware on WebSocket + REST
  - Environment variable token storage
  - 401 Unauthorized for invalid tokens

- ⏳ **TASK-044** — Add TLS/SSL support with self-signed certificates
  - Certificate generation script (tools/generate_certs.ps1)
  - HTTPS support (https://localhost:8000)
  - WSS support (wss://localhost:8000/ws/agent-bridge)
  - Agent bridge --insecure flag for self-signed certs

#### WP-0065: Input Validation & Sandboxing (2 points)

- ⏳ **TASK-045** — Implement path sandboxing in agent bridge
  - Block directory traversal (../../etc/passwd)
  - Reject symlinks outside workdir
  - Log suspicious path attempts

- ⏳ **TASK-046** — Add input validation for task dispatch
  - Limit task content to 10,000 chars
  - Validate agent_id format (alphanumeric + hyphens)
  - Sanitize special characters
  - 400 Bad Request for invalid input

#### WP-0066: Rate Limiting & Cost Controls (4 points)

- ⏳ **TASK-047** — Implement rate limiting for dispatch endpoints
  - Per-agent: 10 dispatches/minute
  - Per-IP: 50 dispatches/minute
  - 429 Too Many Requests when exceeded
  - X-RateLimit-* headers

- ⏳ **TASK-048** — Add cost tracking and limits per session
  - Daily limit: $10 (configurable)
  - Session limit: $5 (configurable)
  - Warning at 80% of limit
  - 402 Payment Required when exceeded

#### WP-0067: Audit Logging & Documentation (3 points)

- ⏳ **TASK-049** — Add audit logging for security events
  - Dedicated logs/audit.log file
  - Structured JSON format
  - Log: auth, lifecycle, dispatch, violations
  - Log rotation (100MB max, 10 files)

- ⏳ **TASK-050** — Add security documentation and best practices
  - docs/SECURITY.md comprehensive guide
  - Token generation instructions
  - TLS setup (dev + production)
  - Firewall configuration examples
  - Production deployment checklist
  - Threat model documentation

**Goal:** Production-ready security before enabling advanced features or external access.

---

## V1 Features (After Security Complete)

### EPIC-007 — Multi-Agent Real Orchestration (0/4) ⏳

**Dependencies:** Requires EPIC-009 complete (security first)

- ⏳ **TASK-035** — Implement delegation chain dispatch for remote agents
- ⏳ **TASK-036** — Add tests for delegation chain dispatch
- ⏳ **TASK-037** — Add per-subtask status tracking and API
- ⏳ **TASK-038** — Add chain status visualization to control UI

**Goal:** Enable multi-hop task delegation (Agent A → Agent B → Agent C) with real agents.

---

## Future Work (Later Tasks)

### EPIC-008 — External Control Channels (0/2) 📋

**Dependencies:** Requires EPIC-009 complete (security mandatory for external access)

- 📋 **TASK-039** — Implement messaging bot service for WhatsApp/Telegram
- 📋 **TASK-040** — Add Docker configuration and deployment support

**Goal:** Control agents from mobile (messaging bot) and enable cloud deployment.

---

## Verification Commands

### Current MVP State
```bash
# Backend tests
cd apps/api && python -m pytest

# Frontend build
cd apps/ui && npm run build

# Agent bridge help
python tools/agent_bridge/bridge.py --help

# Git status
git status -sb
```

### After Security WPs
```bash
# Generate secure token
python -c "import secrets; print(secrets.token_hex(32))"

# Generate TLS certs
python tools/generate_certs.ps1

# Start with HTTPS/WSS
uvicorn vibeforge_api.main:app --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem

# Connect agent with WSS
python tools/agent_bridge/bridge.py \
  --url wss://localhost:8000/ws/agent-bridge \
  --token <generated-token> \
  --workdir . \
  --insecure

# Check audit logs
cat logs/audit.log | jq

# Verify rate limiting (11th request in 1 minute should fail)
for i in {1..11}; do curl -X POST https://localhost:8000/control/agents/test/dispatch; done
```

---

## Key Files for Reference

- **Canonical tasks:** `docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/tasks.md`
- **Work packages:** `docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/work_packages.md`
- **Manifest:** `docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/manifest.md`
- **Global WP tracker:** `docs/ai/planning/WORK_PACKAGES.md`
- **Control panel guide:** `docs/CONTROL_PANEL_GUIDE.md`
- **Security guide (after WP-0067):** `docs/SECURITY.md`

---

## Execution Roadmap

```
✅ MVP (Complete)
    └── 8 WPs, 36 tasks, 50 points

⏳ V1 Phase 1: Security Hardening (MUST DO FIRST)
    ├── WP-0064: Auth + TLS (4 points)
    ├── WP-0065: Validation (2 points)
    ├── WP-0066: Limits (4 points)
    └── WP-0067: Audit + Docs (3 points)
    Total: 4 WPs, 8 tasks, 13 points

⏳ V1 Phase 2: Delegation Features (After Security)
    ├── WP-0062: Chain Dispatch (6 points)
    └── WP-0063: Chain Status UI (4 points)
    Total: 2 WPs, 4 tasks, 10 points

📋 Later: External Control
    └── EPIC-008 (2 tasks, requires security)
```

---

**Legend:**
- ✅ Done — Task completed and verified
- ⏳ Queued — Task ready to implement (dependencies met)
- 📋 Later — Deferred to future release
- 🚫 Blocked — Cannot proceed (missing dependency or decision)
