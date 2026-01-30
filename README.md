# VibeForge

**Control real Claude Code agents from a single web interface.** Dispatch tasks, monitor execution, and manage multiple agents running across different machines or projects.

This is a **private solo project** - this README is optimized for quick context switching between machines.

---

## 📍 Current Status

**MVP Complete + Security Hardening Complete (V1)**

- ✅ **Control Panel** (`/control`) - Manage multiple Claude Code agents from a web UI
- ✅ **Agent Bridge Service** - Connects remote agents to the control plane via WebSocket
- ✅ **Multi-machine Support** - Control agents on laptop, PC, or remote machines over LAN
- ✅ **Authentication** - Token-based auth with secure validation
- ✅ **TLS/WSS** - Encrypted connections with self-signed certs for development
- ✅ **Rate Limiting** - Per-agent and per-IP dispatch limits (configurable)
- ✅ **Cost Tracking** - Session and daily cost limits with warnings
- ✅ **Audit Logging** - Structured JSON logs for all security events
- ✅ **Input Validation** - Path sandboxing and content sanitization
- 🔄 **Simulation Mode** (`/simulation`) - Browser-based workflow sandbox (legacy, still functional)

**Next:** V1 features (delegation chains, chain status tracking)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **Claude Code CLI** (for agent bridge)
- **Git**

### 1. Clone & Setup

```powershell
# Clone repository
git clone https://github.com/Darkpunkki/v-forge.git
cd v-forge

# Generate authentication token
. .\set-token.ps1 -Generate
# Save the displayed token - you'll need it for all machines!
```

### 2. Setup API Server

```powershell
cd apps\api

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set token (from step 1)
. ..\..\set-token.ps1

# Run tests
python -m pytest

# Start API server
uvicorn vibeforge_api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Setup UI

```powershell
cd apps\ui

# Install dependencies
npm install

# Set token (from step 1)
. ..\..\set-token.ps1

# Start UI dev server
npm run dev
# UI available at: http://localhost:5173
```

### 4. Start an Agent

**On the same machine (or any machine with network access):**

```powershell
cd v-forge

# Set token (use same token from step 1)
. .\set-token.ps1

# Verify Claude Code CLI is installed
claude --version

# Start agent bridge
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id my-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\your\project `
  --heartbeat 15
```

### 5. Use the Control Panel

1. Open `http://localhost:5173/control` in your browser
2. You'll see `my-agent` in the left sidebar (status: **connected**)
3. Click the agent to select it
4. Type a task: `"List all files in the current directory"`
5. Click **Send** and watch the response stream in

**You're now controlling a Claude Code agent from the web!** 🎉

---

## 🔒 Security

Before exposing VibeForge beyond a trusted LAN, read `docs/SECURITY.md` for auth tokens, TLS/WSS setup, rate limits, cost limits, and audit logging.

**Quick security setup:**
```powershell
# Generate TLS certificates (self-signed for dev)
powershell -File tools/generate_certs.ps1

# Start API with HTTPS
uvicorn vibeforge_api.main:app `
  --ssl-keyfile ssl/key.pem `
  --ssl-certfile ssl/cert.pem `
  --host 0.0.0.0

# Connect agent with WSS (encrypted)
python tools/agent_bridge/bridge.py `
  --url wss://localhost:8000/ws/agent-bridge `
  --agent-id my-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\project `
  --insecure
```

---

## 📁 Project Structure

```
v-forge/
├── apps/
│   ├── api/                           # FastAPI backend
│   │   ├── vibeforge_api/
│   │   │   ├── core/                 # Business logic (auth, connection manager, cost tracker, audit logger)
│   │   │   ├── middleware/           # Rate limiter middleware
│   │   │   ├── models/               # Pydantic models (protocols, requests, responses)
│   │   │   ├── routers/              # API endpoints (control, agent_bridge)
│   │   │   └── main.py               # FastAPI app
│   │   ├── tests/                    # Unit tests
│   │   └── requirements.txt
│   └── ui/                            # React+Vite UI
│       ├── src/
│       │   ├── pages/Control.tsx     # Main control panel
│       │   ├── pages/Simulation.tsx  # Simulation sandbox (legacy)
│       │   └── api/controlClient.ts  # API client
│       └── package.json
├── tools/
│   ├── agent_bridge/                  # Agent bridge service
│   │   ├── bridge.py                 # WebSocket client + Claude CLI wrapper
│   │   ├── cli_wrapper.py            # Claude Code CLI invocation with path sandboxing
│   │   └── tests/                    # Bridge tests
│   ├── generate_certs.ps1            # TLS certificate generation
│   └── set-token.ps1                 # Token management script
├── docs/
│   ├── CONTROL_PANEL_GUIDE.md        # Comprehensive usage guide
│   ├── SECURITY.md                   # Security setup and best practices
│   └── forge/                        # Forge pipeline (idea → tasks → WPs)
├── logs/
│   └── audit.log                     # Security event audit log (JSON lines)
├── CLAUDE.md                          # AI DevKit rules
└── README.md                          # This file
```

---

## ✅ What's Implemented (MVP + V1 Security)

### Control Panel Features
- ✅ **Agent Management** - Register, connect, monitor multiple agents
- ✅ **Task Dispatch** - Send tasks to agents via web UI or API
- ✅ **Real-time Streaming** - Server-Sent Events (SSE) for live updates
- ✅ **Follow-up Messages** - Send additional instructions to active tasks
- ✅ **Cost Tracking** - Monitor API usage and spending per session/daily
- ✅ **Connection Dashboard** - See all agents, their status, workdirs, and heartbeats

### Agent Bridge Service
- ✅ **WebSocket Protocol** - Full-duplex communication with API server
- ✅ **Auto-registration** - Agents self-register when connecting
- ✅ **Heartbeat Monitoring** - Detects stale connections and auto-reconnects
- ✅ **Claude Code Integration** - Wraps `claude` CLI for task execution
- ✅ **Path Sandboxing** - Prevents directory traversal and escapes
- ✅ **Progress Streaming** - Reports task progress to control plane

### Security Features
- ✅ **Authentication** - Token-based auth (VIBEFORGE_AUTH_TOKEN)
- ✅ **TLS/WSS** - Encrypted connections with self-signed or CA certs
- ✅ **Rate Limiting** - 10 dispatches/min per agent, 50/min per IP (configurable)
- ✅ **Cost Limits** - $5 session / $10 daily defaults (configurable)
- ✅ **Input Validation** - Agent ID format, content length, special character sanitization
- ✅ **Audit Logging** - All security events logged to `logs/audit.log` (JSON format)
- ✅ **Path Validation** - Directory traversal prevention in agent bridge

### Multi-Machine Support
- ✅ **LAN Deployment** - Run API on one machine, agents on others
- ✅ **Firewall Configuration** - Port 8000 exposure for remote access
- ✅ **Token Sharing** - Same token across all machines for authentication
- ✅ **Remote Workdirs** - Each agent works in its own project directory

---

## 🏗️ Architecture Overview

### Components

```
┌─────────────────────────────────────┐
│  Browser (Control Panel)            │
│  http://localhost:5173/control      │
└────────────┬────────────────────────┘
             │ REST API + SSE
             ▼
┌─────────────────────────────────────┐
│  VibeForge API Server (FastAPI)     │
│  - Authentication middleware        │
│  - Rate limiting middleware         │
│  - Control endpoints                │
│  - Agent bridge WebSocket endpoint  │
│  - Cost tracking + audit logging    │
└────────────┬────────────────────────┘
             │ WebSocket (ws:// or wss://)
             ▼
┌─────────────────────────────────────┐
│  Agent Bridge Service (Python)      │
│  - WebSocket client                 │
│  - Claude Code CLI wrapper          │
│  - Path sandboxing                  │
│  - Progress reporting               │
└────────────┬────────────────────────┘
             │ subprocess
             ▼
┌─────────────────────────────────────┐
│  Claude Code CLI                    │
│  - Runs in agent workdir            │
│  - Executes tasks                   │
│  - Returns results                  │
└─────────────────────────────────────┘
```

### Key Design Principles
- **Real agent control** - Orchestrates actual Claude Code instances, not simulations
- **Multi-machine by design** - API and agents can run on different machines
- **Security-first** - Auth, rate limits, cost controls, audit logs all included
- **WebSocket-based** - Full-duplex communication for real-time updates
- **Provider-agnostic** - Works with any Claude Code CLI setup
- **Workdir isolation** - Each agent operates in its own sandboxed directory
- **Graceful degradation** - Agents auto-reconnect, cost warnings before hard limits

---

## 🔧 Common Commands

### Token Management
```powershell
# Generate new token (first time)
. .\set-token.ps1 -Generate

# Load saved token (subsequent sessions)
. .\set-token.ps1

# Set token from another machine
. .\set-token.ps1 -Token "paste-token-here"

# Verify token is set
echo $env:VIBEFORGE_AUTH_TOKEN
```

### Development
```powershell
# Run all tests
cd apps/api
python -m pytest

# Run specific test suites
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_rate_limiting.py -v
python -m pytest tests/test_cost_limits.py -v
python -m pytest tests/test_input_validation.py -v

# Start API with auto-reload
uvicorn vibeforge_api.main:app --reload --host 0.0.0.0

# Start API with TLS
uvicorn vibeforge_api.main:app `
  --ssl-keyfile ssl/key.pem `
  --ssl-certfile ssl/cert.pem `
  --host 0.0.0.0

# Build UI
cd apps/ui
npm run build
```

### Agent Bridge
```powershell
# Start local agent
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id my-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\project `
  --heartbeat 15

# Start remote agent (connect to PC's API)
python tools/agent_bridge/bridge.py `
  --url ws://192.168.1.100:8000/ws/agent-bridge `
  --agent-id laptop-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\project `
  --heartbeat 15

# Start agent with TLS
python tools/agent_bridge/bridge.py `
  --url wss://192.168.1.100:8000/ws/agent-bridge `
  --agent-id my-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\project `
  --heartbeat 15 `
  --insecure
```

### Monitoring
```powershell
# Check API health
curl http://localhost:8000/health

# List connected agents
curl http://localhost:8000/control/agents `
  -H "Authorization: Bearer $env:VIBEFORGE_AUTH_TOKEN"

# View audit logs
Get-Content logs/audit.log | ConvertFrom-Json

# Tail audit logs (real-time)
Get-Content logs/audit.log -Wait -Tail 10

# Count auth failures
Get-Content logs/audit.log | ConvertFrom-Json | Where-Object { $_.event -eq 'auth_failure' } | Measure-Object
```

---

## 🔑 Environment Variables

### Authentication
```bash
VIBEFORGE_AUTH_TOKEN=<your-token>           # Single token
VIBEFORGE_AUTH_TOKENS=token1,token2         # Multiple tokens (comma-separated)
VIBEFORGE_AUTH_TOKEN_FILE=path/to/tokens    # Load tokens from file
```

### Rate Limiting
```bash
VIBEFORGE_RATE_LIMIT_AGENT_PER_MIN=10       # Per-agent limit (default: 10)
VIBEFORGE_RATE_LIMIT_IP_PER_MIN=50          # Per-IP limit (default: 50)
```

### Cost Tracking
```bash
VIBEFORGE_DAILY_COST_LIMIT_USD=10           # Daily limit (default: 10)
VIBEFORGE_SESSION_COST_LIMIT_USD=5          # Session limit (default: 5)
VIBEFORGE_COST_WARNING_THRESHOLD=0.8        # Warning at 80% (default: 0.8)
VIBEFORGE_COST_PER_1K_TOKENS_USD=0          # Token-based cost (default: 0 = disabled)
```

### Audit Logging
```bash
VIBEFORGE_AUDIT_LOG_PATH=logs/audit.log     # Log file path
VIBEFORGE_AUDIT_LOG_LEVEL=INFO              # Log level
VIBEFORGE_AUDIT_LOG_MAX_BYTES=104857600     # Max size (default: 100MB)
VIBEFORGE_AUDIT_LOG_BACKUP_COUNT=10         # Backup count (default: 10)
```

---

## 📋 Development Workflow

This project uses the **Forge Pipeline** for structured development:

1. **Ideas** → Normalized concept summaries
2. **Concepts** → Epics with invariants and scope targets
3. **Epics** → Features with acceptance criteria
4. **Features** → Tasks with implementation details
5. **Tasks** → Work Packages (WPs) for execution

**Current tracking:**
- Main backlog: `docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/tasks.md`
- Work packages: `docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/work_packages.md`
- Quick status: `docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/task_status.md`

**Progress:**
- ✅ MVP: 8 WPs, 36 tasks complete (100%)
- ✅ V1 Security: 4 WPs, 8 tasks complete (100%)
- ⏳ V1 Features: 2 WPs, 4 tasks queued (delegation chains)

---

## 📚 Documentation

- **[CONTROL_PANEL_GUIDE.md](docs/CONTROL_PANEL_GUIDE.md)** - Comprehensive usage guide
  - Quick start, multi-machine setup, troubleshooting
  - PC + Laptop setup scenarios
  - Making agents persistent
  - API reference

- **[SECURITY.md](docs/SECURITY.md)** - Security setup and best practices
  - Authentication tokens
  - TLS/WSS configuration
  - Firewall rules
  - Rate and cost limits
  - Audit logging
  - Production deployment checklist
  - Threat model

---

## 💡 Use Cases

### Single Machine Development
Run the API, UI, and agent on one machine. Control your local Claude Code instance from a web interface.

### Multi-Project Management
Run multiple agents, each in a different project directory. Switch between them in the UI.

### Laptop + PC Workflow
Run the API on your always-on PC, control agents from your laptop's browser, dispatch work to either machine.

### Team Collaboration
Run API server on a shared machine, team members run agents on their own machines for their own projects.

---

## 🚧 What's Not Implemented (Yet)

### V1 Features (Queued)
- ⏳ **Delegation Chains** - Agent A delegates to Agent B, who delegates to Agent C
- ⏳ **Chain Status UI** - Visualize multi-hop delegation chains with status per subtask

### Later Scope
- 📋 **WhatsApp/Telegram Control** - Control agents from messaging apps
- 📋 **Cloud Deployment** - Docker + managed hosting setup
- 📋 **Local LLM Support** - Run agents with local models (Ollama, etc.)



---

## 📝 Notes

- **Python version**: Tested on Python 3.12, should work on 3.11+
- **Claude Code CLI**: Must be installed and configured (`claude --version`)
- **Audit logs**: Located at `logs/audit.log` (JSON lines format)
- **SSL certificates**: Self-signed certs in `ssl/` directory (gitignored)
- **Token file**: `.vibeforge-token` stores your auth token locally (gitignored)
- **Test coverage**: 695 tests, covering auth, rate limiting, cost tracking, validation, control, simulation

---

## 🤝 Contributing (Solo Project)

This is a private solo project, but the structure follows these principles:
- Work packages drive implementation
- All security features have tests
- Documentation stays up-to-date with code
- Changes are tracked via Forge pipeline (IDEA → EPIC → TASK → WP)

---

## 📄 License

Private project - All rights reserved.
