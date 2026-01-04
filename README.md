# VibeForge (Cloud-first MVP, local later) — Project Skeleton

This repo is a starting point for the VibeForge factory pipeline:
- UI (React+Vite) drives a constrained questionnaire (no free text)
- Local API (FastAPI) orchestrates sessions and runs the build pipeline
- Provider-agnostic LLM layer (OpenAI now; local provider later)
- Workspace + patch-apply + verification loop

## Prereqs
- Python 3.11+
- Node.js (per Vite requirements; see Vite docs)

## Quick start (dev)
### 1) Backend API
```bash
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
uvicorn vibeforge_api.main:app --reload --port 8000
```

### 2) UI
```bash
cd apps/ui
npm install
npm run dev
```

Open UI at http://localhost:5173
API at http://localhost:8000/docs

## Repo layout
See `docs/architecture/` and `vibeforge_master_checklist.md`.
