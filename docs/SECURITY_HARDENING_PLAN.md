# Security Hardening Plan — EPIC-009

**Created:** 2026-01-29
**Status:** Planned (Queued for V1)
**Priority:** P0 (Must complete before V1 features or external deployment)

---

## 🎯 Why Security Hardening is Critical

### Current MVP Security Issues

| Issue | Risk Level | Impact |
|---|---|---|
| **Hardcoded "secret" token** | 🔴 Critical | Anyone on LAN can control agents |
| **No encryption (ws://, http://)** | 🔴 Critical | Network traffic readable by anyone |
| **No input validation** | 🟠 High | Command injection, directory traversal possible |
| **No rate limiting** | 🟠 High | API abuse, runaway costs |
| **No cost controls** | 🟡 Medium | Unexpected Claude API bills |
| **No audit logging** | 🟡 Medium | No incident response capability |

### Safe For

✅ Home LAN testing (trusted network)
✅ Single-user development
✅ Local experimentation

### NOT Safe For

❌ Public internet exposure
❌ Coffee shop WiFi
❌ Multi-user scenarios
❌ Production workloads
❌ External control (WhatsApp/cloud)

---

## 📋 EPIC-009: Security Hardening Tasks

### Work Package Breakdown

| WP | Title | Tasks | Points | Priority |
|---|---|---|---|---|
| **WP-0064** | Authentication & TLS Foundation | 2 | 4 | 1st |
| **WP-0065** | Input Validation & Sandboxing | 2 | 2 | 2nd |
| **WP-0066** | Rate Limiting & Cost Controls | 2 | 4 | 3rd |
| **WP-0067** | Audit Logging & Documentation | 2 | 3 | 4th |
| **Total** | | **8** | **13** | |

### Execution Order

```
WP-0064 (Auth + TLS)
    ↓ Foundation established
WP-0065 (Validation) + WP-0066 (Limits)
    ↓ Can run in parallel
WP-0067 (Audit + Docs)
    ↓ Security complete
WP-0062 (Delegation features) ← Safe to proceed
```

---

## 🔐 WP-0064: Authentication & TLS Foundation

**Priority:** 1st (Foundational)
**Effort:** 4 points (M + M)
**Dependencies:** MVP complete

### TASK-043: Secure Token Authentication

**Current State:**
```python
--token secret  # Hardcoded, anyone can use
```

**Target State:**
```python
# Generate secure token
token = secrets.token_hex(32)  # 64-char random hex

# Store in environment
VIBEFORGE_TOKEN=<secure-token>

# Agent connects with real token
--token <secure-token>

# Server validates
if not validate_token(request.headers["Authorization"]):
    return 401 Unauthorized
```

**What Changes:**
- New `apps/api/vibeforge_api/core/auth.py` module
- Token validation middleware on WebSocket + REST endpoints
- Agent bridge: Already accepts `--token`, just needs server validation
- Documentation: Token generation instructions

**Acceptance Criteria:**
- ✅ Hardcoded "secret" removed from codebase
- ✅ Secure token generation (32+ byte random)
- ✅ Token validation on all /ws/ and /control/* endpoints
- ✅ 401 Unauthorized for invalid tokens
- ✅ Environment variable token storage
- ✅ Tests pass

---

### TASK-044: TLS/SSL Support

**Current State:**
```bash
# Unencrypted
uvicorn vibeforge_api.main:app --port 8000
ws://localhost:8000/ws/agent-bridge
http://localhost:8000/control/*
```

**Target State:**
```bash
# Generate self-signed certs
python tools/generate_certs.ps1

# Start with TLS
uvicorn vibeforge_api.main:app \
  --ssl-keyfile ssl/key.pem \
  --ssl-certfile ssl/cert.pem

# Encrypted connections
wss://localhost:8000/ws/agent-bridge
https://localhost:8000/control/*

# Agent connects via WSS
python tools/agent_bridge/bridge.py \
  --url wss://localhost:8000/ws/agent-bridge \
  --token <secure> \
  --insecure  # For self-signed certs
```

**What Changes:**
- New `tools/generate_certs.ps1` script (or .sh for Linux)
- Uvicorn SSL context configuration
- Agent bridge: WSS support + cert verification options
- Documentation: TLS setup instructions

**Acceptance Criteria:**
- ✅ Self-signed cert generation script
- ✅ API accepts HTTPS connections
- ✅ WebSocket accepts WSS connections
- ✅ Agent bridge connects via wss://
- ✅ Certificate verification configurable (--insecure flag)
- ✅ Tests pass

**Production Note:** For cloud deployment, use Let's Encrypt (free, auto-renewing). Self-signed certs are for development/testing only.

---

## 🛡️ WP-0065: Input Validation & Sandboxing

**Priority:** 2nd (Attack Prevention)
**Effort:** 2 points (S + S)
**Dependencies:** WP-0064

### TASK-045: Path Sandboxing

**Current Risk:**
```python
# Agent bridge can access ANY path
# Attacker could request: ../../etc/passwd
# Or: C:\Windows\System32\drivers\etc\hosts
```

**Target State:**
```python
def validate_path(path: str, workdir: str) -> bool:
    real_path = os.path.realpath(path)
    real_workdir = os.path.realpath(workdir)

    # Must be inside workdir
    if not real_path.startswith(real_workdir):
        logger.warning(f"Path traversal attempt: {path}")
        return False

    return True
```

**What Changes:**
- Path validation in `tools/agent_bridge/cli_wrapper.py`
- Reject paths with `..` or outside workdir
- Reject symlinks outside workdir
- Log suspicious attempts
- Tests for traversal attacks

**Acceptance Criteria:**
- ✅ Directory traversal blocked
- ✅ Symlinks outside workdir rejected
- ✅ Suspicious paths logged
- ✅ Agent returns error for rejected paths
- ✅ Tests cover attack scenarios

---

### TASK-046: Input Validation & Sanitization

**Current Risk:**
```python
# No validation on task content or agent_id
# Could inject shell commands or special characters
```

**Target State:**
```python
class DispatchTaskRequest(BaseModel):
    content: str = Field(..., max_length=10_000)

    @field_validator('content')
    def validate_content(cls, v):
        if len(v) > 10_000:
            raise ValueError("Task content too long")
        return v

class AgentIdValidator:
    pattern = re.compile(r'^[a-zA-Z0-9-]{1,64}$')

    def validate(agent_id: str):
        if not self.pattern.match(agent_id):
            raise ValueError("Invalid agent_id format")
```

**What Changes:**
- Pydantic validators on `DispatchTaskRequest`
- `agent_id` format validation (alphanumeric + hyphens only)
- Content length limit (10,000 chars)
- Special character sanitization
- Tests for injection attempts

**Acceptance Criteria:**
- ✅ Task content limited to 10,000 chars
- ✅ agent_id format validated
- ✅ Special characters sanitized
- ✅ 400 Bad Request for invalid input
- ✅ Tests cover injection scenarios

---

## 🚦 WP-0066: Rate Limiting & Cost Controls

**Priority:** 3rd (Abuse Prevention)
**Effort:** 4 points (M + M)
**Dependencies:** WP-0064 (needs auth for tracking)

### TASK-047: Rate Limiting

**Current Risk:**
```python
# No limits - can dispatch infinitely
# Abuse of Claude API quota
# Runaway costs
```

**Target State:**
```python
@rate_limit(max_calls=10, period=60)  # Per agent
async def dispatch_task(agent_id: str):
    # Dispatch logic...

# Response headers:
# X-RateLimit-Limit: 10
# X-RateLimit-Remaining: 7
# X-RateLimit-Reset: 1643723400

# When exceeded:
# HTTP 429 Too Many Requests
```

**What Changes:**
- New `apps/api/vibeforge_api/middleware/rate_limiter.py`
- Per-agent limit: 10 dispatches/minute
- Per-IP limit: 50 dispatches/minute (for multi-agent scenarios)
- Rate limit headers in responses
- Tests for rate limiting behavior

**Acceptance Criteria:**
- ✅ Per-agent: 10 dispatches/minute
- ✅ Per-IP: 50 dispatches/minute
- ✅ 429 status when exceeded
- ✅ X-RateLimit-* headers
- ✅ Configurable via environment
- ✅ Tests pass

---

### TASK-048: Cost Tracking & Limits

**Current Risk:**
```python
# No cost controls
# User could rack up $100s in API bills unknowingly
```

**Target State:**
```python
# Configure limits
VIBEFORGE_DAILY_COST_LIMIT=10.00   # $10/day
VIBEFORGE_SESSION_COST_LIMIT=5.00  # $5/session

# Track costs
cost_tracker.add_cost(session_id, cost)

# Check before dispatch
if cost_tracker.get_daily_cost() > daily_limit:
    return 402 Payment Required

# Warn at 80%
if cost_tracker.get_daily_cost() > daily_limit * 0.8:
    emit_warning_event()
```

**What Changes:**
- New `apps/api/vibeforge_api/core/cost_tracker.py`
- Track costs per control session
- Daily limit: $10 (configurable)
- Session limit: $5 (configurable)
- Warning event at 80% of limit
- Block dispatch when exceeded
- Tests for cost limit enforcement

**Acceptance Criteria:**
- ✅ Cost tracked per control session
- ✅ Daily/session limits configurable
- ✅ Warning at 80% of limit
- ✅ Dispatch blocked with 402 when exceeded
- ✅ Cost status in /control/context API
- ✅ Daily reset at midnight UTC
- ✅ Tests pass

---

## 📊 WP-0067: Audit Logging & Documentation

**Priority:** 4th (Monitoring & Guidance)
**Effort:** 3 points (S + M)
**Dependencies:** WP-0064, WP-0065, WP-0066 (all security features)

### TASK-049: Audit Logging

**Current State:**
```python
# Limited logging
# No structured audit trail
# Hard to investigate incidents
```

**Target State:**
```json
// logs/audit.log (JSON lines format)
{"timestamp":"2026-01-29T12:00:00Z","event":"auth_success","agent_id":"my-agent","ip":"192.168.1.100","token_hash":"a3c4..."}
{"timestamp":"2026-01-29T12:00:01Z","event":"agent_register","agent_id":"my-agent","workdir":"C:\\projects\\app","capabilities":[]}
{"timestamp":"2026-01-29T12:00:15Z","event":"task_dispatch","agent_id":"my-agent","task_preview":"Fix the auth bug...","cost":0.05}
{"timestamp":"2026-01-29T12:00:30Z","event":"rate_limit_exceeded","agent_id":"my-agent","ip":"192.168.1.100","limit":10}
{"timestamp":"2026-01-29T12:00:45Z","event":"path_traversal_attempt","agent_id":"my-agent","path":"../../etc/passwd"}
```

**What Changes:**
- New `apps/api/vibeforge_api/core/audit_logger.py`
- Dedicated `logs/audit.log` file
- Structured JSON format (one event per line)
- Log rotation (100MB max, keep 10 files)
- Events logged:
  - Authentication (success/failure)
  - Agent lifecycle (register/disconnect/timeout)
  - Task dispatches (agent_id, task preview, cost)
  - Security violations (rate limits, path traversal, cost limits)

**Acceptance Criteria:**
- ✅ Audit logger configured
- ✅ JSON lines format
- ✅ Log rotation enabled
- ✅ Auth events logged
- ✅ Lifecycle events logged
- ✅ Dispatch events logged
- ✅ Violations logged
- ✅ Level configurable via environment

---

### TASK-050: Security Documentation

**Target:** Comprehensive `docs/SECURITY.md` guide covering all security features.

**Contents:**
1. **Overview**
   - Security posture (what's protected, what's not)
   - Threat model (what attacks are mitigated)
   - Safe vs unsafe deployments

2. **Token Authentication**
   - How to generate secure tokens
   - Token rotation procedures
   - Environment variable configuration

3. **TLS/SSL Setup**
   - Self-signed certs for development
   - Let's Encrypt for production
   - Certificate renewal procedures

4. **Firewall Configuration**
   - Windows Firewall rules
   - Linux iptables/ufw examples
   - Port requirements (8000, 5173)

5. **Workdir Isolation**
   - Best practices (dedicated directories)
   - What NOT to use as workdir
   - Permission requirements

6. **Rate Limits & Cost Controls**
   - Configuration examples
   - How to adjust limits
   - Monitoring recommendations

7. **Audit Log Monitoring**
   - How to read logs
   - What events indicate attacks
   - Log analysis examples

8. **Production Deployment Checklist**
   - Pre-deployment security review
   - Required configurations
   - Testing procedures
   - Monitoring setup

9. **Incident Response**
   - What to do if compromised
   - How to revoke tokens
   - Log analysis for forensics

**Acceptance Criteria:**
- ✅ docs/SECURITY.md created
- ✅ All 9 sections complete
- ✅ Code examples provided
- ✅ CONTROL_PANEL_GUIDE.md links to SECURITY.md
- ✅ README.md includes security notice

---

## 🚀 After Security: V1 Features

Once EPIC-009 is complete, it's **safe** to proceed with:

### EPIC-007: Multi-Agent Orchestration
- WP-0062: Delegation chain dispatch
- WP-0063: Chain status tracking + UI

### EPIC-008: External Control Channels (Later)
- TASK-039: WhatsApp/Telegram bot
- TASK-040: Docker deployment + WSS

---

## 📊 Project Status After Security

```
✅ MVP Complete (36 tasks, 8 WPs)
    └── Basic agent control working on trusted LAN

⏳ V1 Security (8 tasks, 4 WPs) ← YOU ARE HERE
    ├── Authentication + TLS
    ├── Input validation
    ├── Rate limits + cost controls
    └── Audit logging + docs

⏳ V1 Features (4 tasks, 2 WPs) ← After security
    └── Delegation chains

📋 Later (2 tasks) ← After V1
    └── External control (WhatsApp/cloud)
```

---

## 🎯 Recommended Execution

### Week 1: Foundation
- Execute WP-0064 (Auth + TLS)
- Test with secure tokens + WSS

### Week 2: Protection
- Execute WP-0065 (Validation)
- Execute WP-0066 (Limits)
- Test attack scenarios

### Week 3: Monitoring
- Execute WP-0067 (Audit + Docs)
- Review security documentation
- Run security checklist

### Week 4: V1 Features
- Execute WP-0062 (Delegation)
- Execute WP-0063 (Status UI)

---

## ✅ Verification Checklist

After completing EPIC-009, verify:

- [ ] Hardcoded "secret" removed from codebase
- [ ] Secure token generation documented
- [ ] Token validation active on all endpoints
- [ ] HTTPS/WSS connections working
- [ ] Self-signed certs generated successfully
- [ ] Path traversal attempts blocked
- [ ] Input validation rejecting invalid requests
- [ ] Rate limiting enforced (11th dispatch in 1 min fails)
- [ ] Cost limits enforced (dispatch blocked when exceeded)
- [ ] Audit log populated with structured events
- [ ] docs/SECURITY.md comprehensive guide complete
- [ ] Production deployment checklist available

---

## 🎉 Success Metrics

**Before EPIC-009:**
- ⚠️ Vulnerable to LAN attacks
- ⚠️ Not safe for untrusted networks
- ⚠️ No cost controls

**After EPIC-009:**
- ✅ Production-ready security
- ✅ Safe for LAN + cloud deployment
- ✅ Attack mitigation in place
- ✅ Cost controls active
- ✅ Audit trail available
- ✅ Ready for external control channels

---

**Next Command:** `/work-wp IDEA-0003-vibeforge-is-pivoting WP-0064`
