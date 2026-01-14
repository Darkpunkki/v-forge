# VibeForge

**An AI-powered application factory** that generates working apps from structured questionnaires (no free-text input). Cloud-first foundation with a post-MVP focus on observability, simulation, and local LLM readiness.

This is a **private solo project** - this README is optimized for quick context switching between machines.

---

## 📍 Current Stage (Post-MVP)

- **Session orchestration is live**: phase-guarded questionnaire → plan → execution pipeline with result gating.
- **Control panel exists**: operators can monitor sessions, view events, and configure agent workflows.
- **Simulation mode is scaffolded**: tick engine + API endpoints exist, but the execution loop is not yet wired.
- **Local LLM seam is ready**: router + provider stubs support future local inference.

---

## 🚀 Quick Start (New Machine Setup)

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **Git**

### 1. Clone & Setup API
```bash
git clone https://github.com/Darkpunkki/v-forge.git
cd v-forge/apps/api

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and add OPENAI_API_KEY
# (Or use stub mode with VIBEFORGE_LLM_MODE=stub)
echo OPENAI_API_KEY=your_key_here > .env
```

### 2. Run Tests
```bash
# From apps/api with venv activated
pytest -v

# Run specific test files
pytest tests/test_sessions.py -v
pytest tests/test_workspace.py tests/test_patch.py tests/test_artifacts.py -v
```

### 3. Start API Server
```bash
# From apps/api with venv activated
uvicorn vibeforge_api.main:app --reload --port 8000

# API docs available at: http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

### 4. Start the UI (optional)
```bash
cd ../ui
npm install
npm run dev
```

> The UI defaults to `http://localhost:8000` unless `VITE_API_BASE` is set.

---

## 📁 Project Structure

```
v-forge/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── vibeforge_api/
│   │   │   ├── core/          # Business logic
│   │   │   ├── models/        # Pydantic models
│   │   │   ├── routers/       # API endpoints (sessions + control)
│   │   │   └── main.py        # FastAPI app
│   │   ├── tests/             # Unit tests
│   │   └── requirements.txt
│   └── ui/                     # React+Vite UI (session + control panel)
├── configs/                    # Stack presets, policies
├── docs/ai/                    # AI-assisted dev documentation
├── orchestration/              # Orchestrator + coordinator logic
├── models/                     # Model router + provider implementations
├── schemas/                    # JSON schemas (BuildSpec, TaskGraph, etc.)
├── vibeforge_master_checklist.md  # Canonical backlog
├── CLAUDE.md                   # AI DevKit rules
└── README.md                   # This file
```

---

## ✅ Progress by Epic (Post-MVP snapshot)

### Session orchestration & phase enforcement (WP-0001, WP-0006)
- Phase-aware session flow: questionnaire → plan review → execution → result.
- Clarification flow for gated execution questions.

### Workspace, artifacts, and verification (WP-0002, WP-0003, WP-0004)
- Workspace isolation per session.
- Artifact logging and event stream storage.
- Safety gates and verification harness in the backend core.

### Orchestration & agent framework (WP-0006, VF-100+)
- LLM orchestration for concept/task graph generation.
- Agent execution via Direct LLM adapter.
- Deterministic stub LLM for safe/no-spend runs.

### Control panel observability (VF-190+)
- Admin endpoints for session listing, SSE events, and LLM trace inspection.
- Workflow configuration for agents, roles/models, flow graph, and main task.

### Control-mode simulation scaffolding (VF-190+)
- Tick engine + simulation API endpoints exist but are not yet connected.
- UI lacks tick controls and agent message views.

### UI shell & routing (WP-0007)
- Session screens for questionnaire, plan review, progress, clarification, and result.
- Control panel screen for monitoring and workflow configuration.

---

## 🏗️ Architecture Overview

**Core Components:**
1. **UI** (React+Vite): Questionnaire flow + control panel
2. **Local API** (FastAPI): Session orchestration, phase management, control endpoints
3. **Session Coordinator**: Drives questionnaire → build spec → concept → plan → execution flow
4. **Workspace Manager**: Creates isolated workspaces per session
5. **Patch Applier**: Safely applies diffs with path validation
6. **Model Layer**: Provider-agnostic (OpenAI now, local later)
7. **Agent Framework**: Pluggable (direct calls MVP, graph-based frameworks later)
8. **Verification + Gates**: Build/test/safety checks per task

**Key Design Principles:**
- No free-text user input (multiple choice only)
- Session phases prevent illegal transitions
- Path traversal protection on all file operations
- Workspace isolation per session
- Provider-agnostic model interface for future local LLM support
- Gate pipeline validates all operations before execution
- Allowlisted command execution with timeout protection

---

## 🔑 Environment Variables

Create `apps/api/.env`:
```
OPENAI_API_KEY=sk-...
# Optional:
# VIBEFORGE_LLM_MODE=stub
# VIBEFORGE_NO_SPEND=true
```

---

## 🔧 Common Commands

### Testing
```bash
# All tests
cd apps/api && pytest

# With coverage
pytest --cov=vibeforge_api --cov-report=html

# Specific module
pytest tests/test_sessions.py -v

# Watch mode (requires pytest-watch)
ptw
```

### Development
```bash
# Start API with auto-reload
cd apps/api
uvicorn vibeforge_api.main:app --reload

# Check API docs
# http://localhost:8000/docs

# Format code (if black/ruff installed)
black vibeforge_api/
ruff check vibeforge_api/
```

### Git Workflow
```bash
# Check what's completed
grep -E "^- \[x\]" vibeforge_master_checklist.md

# Check next tasks
grep -E "^- \[ \]" vibeforge_master_checklist.md | head -10

# Current work package
cat docs/ai/planning/WORK_PACKAGES.md | grep -A 10 "Status: Queued" | head -15
```

---

## 📋 Development Workflow

This project uses **Work Packages (WPs)** for structured development. The post-MVP focus is on:
- Wiring simulation tick execution into the control endpoints
- Hardening orchestration and verification flows
- Preparing local model provider integrations

For detailed planning, see `docs/ai/planning/WORK_PACKAGES.md` and `vibeforge_master_checklist.md`.

---

## 💡 Quick Reference

### Check API is working
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","service":"vibeforge-api"}
```

### Create a test session
```bash
curl -X POST http://localhost:8000/sessions
# Returns: {"session_id":"...","phase":"QUESTIONNAIRE"}
```

---

## 📝 Notes

- **Workspaces**: Generated session workspaces are gitignored (`workspaces/`).
- **Python version**: Tested on Python 3.12, should work on 3.11+.
- **UI**: Session flow + control panel are wired to the API, but simulation controls are not yet surfaced.
- **Focus**: Post-MVP hardening, observability, and simulation execution.
