# VibeForge

**An AI-powered application factory** that generates working apps from structured questionnaires (no free-text input). Cloud-first MVP with plans for local LLM support.

This is a **private solo project** - this README is optimized for quick context switching between machines.

---

## 🎯 What Works Now

### ✅ Implemented (WP-0001, WP-0002)
- **Local UI API (FastAPI)**: Session management with phase-safe transitions
  - POST /sessions - Create session
  - GET /sessions/{id}/question - Get next question
  - POST /sessions/{id}/answers - Submit answer
  - GET /sessions/{id}/progress - View progress
  - Phase validation and error handling
- **Workspace Management**: Isolated workspaces per session (repo/ + artifacts/)
- **Patch Application**: Safe unified diff application with path traversal prevention
- **Artifact Storage**: Metadata persistence for traceability

### 🚧 Next Up (WP-0003, WP-0004)
- Command runner + verification harness
- Gates pipeline (safety checks)
- Full orchestration + agent framework

---

## 🚀 Quick Start (New Machine Setup)

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** (for UI, when implemented)
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

---

## 📁 Project Structure

```
v-forge/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── vibeforge_api/
│   │   │   ├── core/          # Business logic
│   │   │   │   ├── session.py       # Session model & store
│   │   │   │   ├── questionnaire.py # Question engine
│   │   │   │   ├── workspace.py     # Workspace manager (VF-110, VF-111)
│   │   │   │   ├── patch.py         # Patch applier (VF-113, VF-114)
│   │   │   │   └── artifacts.py     # Artifact store (VF-115)
│   │   │   ├── models/        # Pydantic models
│   │   │   ├── routers/       # API endpoints
│   │   │   └── main.py        # FastAPI app
│   │   ├── tests/             # Unit tests (46 tests, all passing)
│   │   └── requirements.txt
│   └── ui/                     # React+Vite UI (skeleton only)
├── configs/                    # Stack presets, policies
├── docs/ai/                    # AI-assisted dev documentation
│   ├── planning/
│   │   ├── WORK_PACKAGES.md   # Near-term work queue
│   │   ├── WP-0001_*.md       # Completed: API endpoints
│   │   └── WP-0002_*.md       # Completed: Workspace + patching
│   ├── requirements/
│   ├── design/
│   └── ...
├── schemas/                    # JSON schemas (BuildSpec, TaskGraph, etc.)
├── vibeforge_master_checklist.md  # Canonical backlog (VF-001 to VF-167)
├── CLAUDE.md                   # AI DevKit rules
└── README.md                   # This file
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

This project uses **Work Packages (WPs)** for structured development:

1. **Check current status**: See `docs/ai/planning/WORK_PACKAGES.md`
2. **Next WP**: WP-0003 (Command runner + verification)
3. **Master backlog**: `vibeforge_master_checklist.md` (VF-001 to VF-167)
4. **Execute**: Use `/execute-plan` in Claude Code to run next WP
5. **Verify**: Each WP has specific test commands
6. **Update**: Check off VF tasks in master checklist when complete

### Current Progress
- ✅ WP-0001: Local UI API completion (8 VF tasks)
- ✅ WP-0002: Workspace + patch apply safety (5 VF tasks)
- ⏭️ WP-0003: Command runner + verification harness (4 VF tasks)
- ⏭️ WP-0004: Gates pipeline (6 VF tasks)

---

## 🏗️ Architecture Overview

**Core Components:**
1. **UI** (React+Vite): Constrained questionnaire interface (no free text)
2. **Local API** (FastAPI): Session orchestration, phase management
3. **Session Coordinator**: Drives questionnaire → build spec → concept → plan → execution flow
4. **Workspace Manager**: Creates isolated workspaces per session
5. **Patch Applier**: Safely applies diffs with path validation
6. **Model Layer**: Provider-agnostic (OpenAI now, local later)
7. **Agent Framework**: Pluggable (direct calls MVP, LangGraph/CrewAI later)
8. **Verification**: Build/test/smoke checks per task

**Key Design Principles:**
- No free-text user input (multiple choice only)
- Session phases prevent illegal transitions
- Path traversal protection on all file operations
- Workspace isolation per session
- Provider-agnostic model interface for future local LLM support

---

## 🔑 Environment Variables

Create `apps/api/.env`:
```
OPENAI_API_KEY=sk-...
```

---

## 📚 Key Documentation

- **Work Packages**: `docs/ai/planning/WORK_PACKAGES.md` - Current sprint
- **Master Checklist**: `vibeforge_master_checklist.md` - All VF tasks
- **Design Docs**: `docs/ai/design/` - Architecture decisions
- **AI Rules**: `CLAUDE.md` - Development guidelines for AI assistance

---

## 🧪 Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| Sessions API | 10 | ✅ Pass |
| Workspace | 12 | ✅ Pass |
| Patch Applier | 11 | ✅ Pass |
| Artifacts | 13 | ✅ Pass |
| **Total** | **46** | ✅ **All Pass** |

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

### Run next work package
```bash
# In Claude Code
/execute-plan
```

---

## 📝 Notes

- **Workspaces**: Generated session workspaces are gitignored (`workspaces/`)
- **Python version**: Tested on Python 3.12, should work on 3.11+
- **No UI yet**: UI is skeleton only, API is functional
- **MVP focus**: Building core plumbing first, polish later
