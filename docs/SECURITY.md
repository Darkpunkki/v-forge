# Security Guide

This document describes security configuration and best practices for running VibeForge in local, LAN, and production environments.

---

## Quick Checklist

- [ ] Generate strong auth tokens (do not reuse defaults)
- [ ] Enable TLS/WSS for any non-local use
- [ ] Restrict agent workdirs to a safe project root
- [ ] Configure rate limits and cost limits
- [ ] Monitor audit logs
- [ ] Harden firewall rules

---

## Authentication Tokens

### Generate a token (recommended)
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### Configure tokens
Set one token:
```powershell
$env:VIBEFORGE_AUTH_TOKEN = "<token>"
```

Or multiple tokens (comma-separated):
```powershell
$env:VIBEFORGE_AUTH_TOKENS = "token1,token2"
```

Optional: load from a file (one token per line):
```powershell
$env:VIBEFORGE_AUTH_TOKEN_FILE = "C:\path\to\tokens.txt"
```

---

## TLS / HTTPS / WSS

### Development (self-signed)
```powershell
python tools/generate_certs.ps1
uvicorn vibeforge_api.main:app --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem
```

Agent bridge (dev only):
```powershell
python tools/agent_bridge/bridge.py `
  --url wss://localhost:8000/ws/agent-bridge `
  --agent-id my-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\project `
  --heartbeat 15 `
  --insecure
```

### Production (recommended)
- Terminate TLS with a reverse proxy (nginx, Caddy, or Traefik)
- Use valid certificates (Let's Encrypt or managed certs)
- Disable `--insecure` for all agents

---

## Firewall Rules (Examples)

### Windows (PowerShell)
```powershell
# Allow API port for LAN (adjust as needed)
New-NetFirewallRule -DisplayName "VibeForge API" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000
```

### Linux (ufw)
```bash
sudo ufw allow 8000/tcp
sudo ufw status
```

---

## Workdir Isolation

- Use a dedicated project directory for each agent.
- Do not point `--workdir` at system directories (e.g., `C:\Windows`, `/etc`).
- Avoid running agents as admin/root.
- Consider separate OS users for untrusted workflows.

---

## Rate Limits

Environment variables:
- `VIBEFORGE_RATE_LIMIT_AGENT_PER_MIN` (default: 10)
- `VIBEFORGE_RATE_LIMIT_IP_PER_MIN` (default: 50)

When exceeded, dispatch returns HTTP 429 with `X-RateLimit-*` headers.

---

## Cost Limits

Environment variables:
- `VIBEFORGE_DAILY_COST_LIMIT_USD` (default: 10)
- `VIBEFORGE_SESSION_COST_LIMIT_USD` (default: 5)
- `VIBEFORGE_COST_WARNING_THRESHOLD` (default: 0.8)
- `VIBEFORGE_COST_PER_1K_TOKENS_USD` (default: 0; set if you want token-based cost estimates)

When exceeded, dispatch returns HTTP 402.

---

## Audit Logging

Audit log location (default):
- `logs/audit.log`

Log rotation defaults:
- 100MB max file size
- 10 backups

Environment variables:
- `VIBEFORGE_AUDIT_LOG_PATH`
- `VIBEFORGE_AUDIT_LOG_LEVEL`
- `VIBEFORGE_AUDIT_LOG_MAX_BYTES`
- `VIBEFORGE_AUDIT_LOG_BACKUP_COUNT`

### Monitoring
- Tail logs for security events: `auth_failure`, `rate_limit_exceeded`, `cost_limit_exceeded`, `path_validation_failed`
- Alert on repeated failures or spikes

---

## Production Deployment Checklist

- [ ] TLS enabled and verified
- [ ] Auth tokens rotated and stored securely
- [ ] Firewall rules limited to known IPs
- [ ] Rate/cost limits configured
- [ ] Audit log storage monitored (disk space + rotation)
- [ ] Agents run with least privilege
- [ ] Backup / incident response plan

---

## Threat Model (High Level)

### Mitigations
- **Unauthorized access**: token-based auth + audit logs
- **Network eavesdropping**: HTTPS/WSS
- **Abuse / DoS**: rate limits per agent/IP
- **Cost overruns**: daily and session cost limits
- **Path traversal**: workdir sandboxing

### Not addressed
- Full multi-tenant isolation
- Advanced user impersonation protection
- Supply-chain compromise

---

If you plan to expose VibeForge beyond a trusted LAN, complete all items above and run a security review.
