# WP-0022 — Control Panel Architecture and Routing

## VF Tasks Included
- [ ] VF-170 — Control panel architecture (separate admin UI route)
  - **Files:**
    - `apps/ui/src/screens/control/ControlPanel.tsx` (main control panel layout)
    - `apps/ui/src/api/controlClient.ts` (control-specific API client)
    - `apps/api/vibeforge_api/routers/control.py` (control API endpoints)
  - **Tests:**
    - `apps/api/tests/test_control_api.py` (API endpoint tests)
    - `apps/ui/src/screens/control/__tests__/ControlPanel.test.tsx` (UI tests)
  - **Verify:** `cd apps/ui && npm run build && npm run dev` - Control panel accessible at /control

## Goal
Create the foundational control panel UI architecture separate from the end-user workflow, with real-time session monitoring capabilities via WebSocket or Server-Sent Events.

## Dependencies
- ✅ WP-0021 (EventLog + structured events) - provides event stream for real-time updates

## Why Critical
All subsequent control UI features (WP-0023 through WP-0027) build on this foundation. Without the /control route, WebSocket/SSE infrastructure, and base layout, no monitoring dashboards can be built.

## Execution Steps

### 1. Backend: Control API Endpoints

**Intent:** Create API endpoints for control panel data access and event streaming.

**Implementation:**

Create `apps/api/vibeforge_api/routers/control.py`:
```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime

router = APIRouter(prefix="/control", tags=["control"])

@router.get("/sessions")
async def list_all_sessions():
    """List all sessions with metadata for control panel."""
    from vibeforge_api.core.artifacts import SessionArtifactQuery
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    query = SessionArtifactQuery(workspace_manager.workspace_root)

    sessions = query.query_sessions_by_date()

    return {
        "sessions": sessions,
        "total": len(sessions),
    }

@router.get("/sessions/{session_id}/events")
async def stream_session_events(session_id: str):
    """Stream session events via Server-Sent Events (SSE)."""
    from vibeforge_api.core.event_log import EventLog
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    workspace_path = workspace_manager.workspace_root / session_id
    event_log_path = workspace_path / "events.jsonl"

    if not event_log_path.exists():
        raise HTTPException(status_code=404, detail="Event log not found")

    event_log = EventLog(str(event_log_path))

    async def event_generator():
        """Generate SSE events."""
        # Send existing events first
        events = event_log.get_events()
        for event in events:
            yield {
                "event": "session_event",
                "data": json.dumps(event.to_dict()),
            }

        # Then stream new events (poll for updates)
        last_count = len(events)
        while True:
            await asyncio.sleep(1)  # Poll every second

            # Check for new events
            current_events = event_log.get_events()
            if len(current_events) > last_count:
                new_events = current_events[last_count:]
                for event in new_events:
                    yield {
                        "event": "session_event",
                        "data": json.dumps(event.to_dict()),
                    }
                last_count = len(current_events)

    return EventSourceResponse(event_generator())

@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current session status for control panel."""
    from vibeforge_api.core.session import session_store

    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "phase": session.phase.value,
        "active_task_id": session.active_task_id,
        "completed_tasks": len(session.completed_task_ids),
        "failed_tasks": len(session.failed_task_ids),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }

@router.get("/active")
async def get_active_sessions():
    """Get all active sessions (not in COMPLETE or FAILED state)."""
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models.types import SessionPhase

    all_sessions = session_store.list_sessions()
    active = []

    for session in all_sessions:
        if session.phase not in {SessionPhase.COMPLETE, SessionPhase.FAILED}:
            active.append({
                "session_id": session.id,
                "phase": session.phase.value,
                "active_task_id": session.active_task_id,
                "updated_at": session.updated_at.isoformat(),
            })

    return {
        "active_sessions": active,
        "total": len(active),
    }
```

Add to `apps/api/vibeforge_api/main.py`:
```python
from vibeforge_api.routers import control

app.include_router(control.router)
```

**Tests:**
- `test_list_all_sessions()` - verify session listing
- `test_stream_session_events()` - verify SSE streaming
- `test_get_session_status()` - verify status endpoint
- `test_get_active_sessions()` - verify active filtering

---

### 2. Frontend: Control Panel Route and Layout

**Intent:** Create separate /control route with base layout for control panel.

**Implementation:**

Update `apps/ui/src/App.tsx` to add control route:
```tsx
import ControlPanel from './screens/control/ControlPanel';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Existing end-user routes */}
        <Route path="/" element={<Home />} />
        <Route path="/questionnaire" element={<Questionnaire />} />
        <Route path="/plan-review" element={<PlanReview />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/clarification" element={<Clarification />} />
        <Route path="/result" element={<Result />} />

        {/* NEW: Control panel route */}
        <Route path="/control" element={<ControlPanel />} />
        <Route path="/control/:sessionId" element={<ControlPanel />} />
      </Routes>
    </BrowserRouter>
  );
}
```

Create `apps/ui/src/screens/control/ControlPanel.tsx`:
```tsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import './ControlPanel.css';

interface ControlPanelProps {}

const ControlPanel: React.FC<ControlPanelProps> = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const [activeSessions, setActiveSessions] = useState<any[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(sessionId || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActiveSessions();
    const interval = setInterval(fetchActiveSessions, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchActiveSessions = async () => {
    try {
      const response = await fetch('http://localhost:8000/control/active');
      const data = await response.json();
      setActiveSessions(data.active_sessions);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch active sessions:', error);
      setLoading(false);
    }
  };

  return (
    <div className="control-panel">
      {/* Header */}
      <header className="control-header">
        <h1>🎛️ VibeForge Control Panel</h1>
        <div className="control-meta">
          <span className="active-count">
            {activeSessions.length} active session{activeSessions.length !== 1 ? 's' : ''}
          </span>
        </div>
      </header>

      {/* Main Layout: Sidebar + Content */}
      <div className="control-layout">
        {/* Left Sidebar: Session List */}
        <aside className="session-sidebar">
          <h2>Active Sessions</h2>
          {loading ? (
            <div className="loading">Loading...</div>
          ) : activeSessions.length === 0 ? (
            <div className="no-sessions">No active sessions</div>
          ) : (
            <ul className="session-list">
              {activeSessions.map((session) => (
                <li
                  key={session.session_id}
                  className={`session-item ${selectedSession === session.session_id ? 'selected' : ''}`}
                  onClick={() => setSelectedSession(session.session_id)}
                >
                  <div className="session-id">{session.session_id.substring(0, 8)}</div>
                  <div className="session-phase">{session.phase}</div>
                  {session.active_task_id && (
                    <div className="session-task">Task: {session.active_task_id}</div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* Main Content Area */}
        <main className="control-content">
          {selectedSession ? (
            <div className="session-details">
              <h2>Session: {selectedSession.substring(0, 8)}</h2>
              <p className="placeholder">
                Control panel widgets will be added in WP-0023 through WP-0027.
              </p>
              <div className="widgets-placeholder">
                <div className="widget-slot">📊 Agent Dashboard (WP-0023)</div>
                <div className="widget-slot">💰 Token Usage (WP-0023)</div>
                <div className="widget-slot">🕸️ Agent Graph (WP-0024)</div>
                <div className="widget-slot">📅 Timeline (WP-0024)</div>
                <div className="widget-slot">🚦 Gate Log (WP-0025)</div>
                <div className="widget-slot">🧭 Model Routing (WP-0025)</div>
                <div className="widget-slot">📈 Analytics (WP-0026)</div>
                <div className="widget-slot">📋 Event Stream (WP-0026)</div>
                <div className="widget-slot">🔍 Prompt Inspector (WP-0027)</div>
                <div className="widget-slot">💵 Cost Analytics (WP-0027)</div>
              </div>
            </div>
          ) : (
            <div className="no-selection">
              <p>Select a session from the sidebar to view details.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default ControlPanel;
```

Create `apps/ui/src/screens/control/ControlPanel.css`:
```css
.control-panel {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #1e1e1e;
  color: #e0e0e0;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.control-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.control-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.control-meta {
  display: flex;
  gap: 1rem;
}

.active-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
}

.control-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.session-sidebar {
  width: 300px;
  background-color: #2d2d2d;
  border-right: 1px solid #444;
  overflow-y: auto;
  padding: 1rem;
}

.session-sidebar h2 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
  color: #aaa;
}

.session-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.session-item {
  padding: 1rem;
  margin-bottom: 0.5rem;
  background-color: #3a3a3a;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-item:hover {
  background-color: #4a4a4a;
}

.session-item.selected {
  background-color: #667eea;
  color: white;
}

.session-id {
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.session-phase {
  font-size: 0.9rem;
  color: #aaa;
}

.session-item.selected .session-phase {
  color: #fff;
}

.session-task {
  font-size: 0.8rem;
  margin-top: 0.5rem;
  opacity: 0.8;
}

.control-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.no-selection {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #777;
  font-size: 1.2rem;
}

.widgets-placeholder {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
}

.widget-slot {
  background-color: #2d2d2d;
  padding: 2rem;
  border-radius: 8px;
  border: 2px dashed #555;
  text-align: center;
  color: #777;
}

.no-sessions,
.loading {
  text-align: center;
  padding: 2rem;
  color: #777;
}
```

---

### 3. API Client for Control Panel

**Intent:** Create typed API client for control-specific endpoints.

**Implementation:**

Create `apps/ui/src/api/controlClient.ts`:
```typescript
const API_BASE = 'http://localhost:8000';

export interface SessionListItem {
  session_id: string;
  created_at: string;
  artifacts: string[];
}

export interface ActiveSession {
  session_id: string;
  phase: string;
  active_task_id: string | null;
  updated_at: string;
}

export interface SessionStatus {
  session_id: string;
  phase: string;
  active_task_id: string | null;
  completed_tasks: number;
  failed_tasks: number;
  created_at: string;
  updated_at: string;
}

export interface SessionEvent {
  event_type: string;
  timestamp: string;
  session_id: string;
  message: string;
  phase?: string;
  task_id?: string;
  agent_role?: string;
  model?: string;
  metadata?: Record<string, any>;
}

export const controlClient = {
  async listAllSessions(): Promise<{ sessions: SessionListItem[]; total: number }> {
    const response = await fetch(`${API_BASE}/control/sessions`);
    if (!response.ok) throw new Error('Failed to list sessions');
    return response.json();
  },

  async getActiveSessions(): Promise<{ active_sessions: ActiveSession[]; total: number }> {
    const response = await fetch(`${API_BASE}/control/active`);
    if (!response.ok) throw new Error('Failed to get active sessions');
    return response.json();
  },

  async getSessionStatus(sessionId: string): Promise<SessionStatus> {
    const response = await fetch(`${API_BASE}/control/sessions/${sessionId}/status`);
    if (!response.ok) throw new Error('Failed to get session status');
    return response.json();
  },

  streamSessionEvents(sessionId: string, onEvent: (event: SessionEvent) => void): EventSource {
    const eventSource = new EventSource(
      `${API_BASE}/control/sessions/${sessionId}/events`
    );

    eventSource.addEventListener('session_event', (e) => {
      const event: SessionEvent = JSON.parse(e.data);
      onEvent(event);
    });

    return eventSource;
  },
};
```

---

## Verification Commands
```bash
# Backend tests
cd apps/api && pytest tests/test_control_api.py -v

# Full test suite
cd apps/api && pytest -v

# Frontend build
cd apps/ui && npm run build

# Frontend dev server
cd apps/ui && npm run dev
# Visit: http://localhost:5173/control
```

## Done Means
- [ ] `/control` route accessible in UI
- [ ] Control panel layout renders with sidebar + content area
- [ ] Backend API endpoints for session listing, status, and event streaming
- [ ] SSE (Server-Sent Events) streaming implemented for real-time updates
- [ ] controlClient.ts provides typed API access
- [ ] All API tests pass (4+ tests for control endpoints)
- [ ] UI builds successfully
- [ ] Control panel shows active sessions in sidebar
- [ ] Foundation ready for WP-0023 through WP-0027 widgets

## Architecture Notes

**Why SSE over WebSocket:**
- Simpler to implement (HTTP-based)
- Auto-reconnection built-in
- Works with standard FastAPI responses
- One-way communication sufficient for event streaming
- Can upgrade to WebSocket later if bidirectional needed

**Dark Theme:**
- Control panel uses dark color scheme (#1e1e1e background)
- Distinct visual identity from end-user UI
- Reduced eye strain for developers monitoring sessions
- Monospace fonts for technical data

**Widget Placeholder Pattern:**
- Shows where future widgets will be added
- References WP numbers for clarity
- Helps visualize final dashboard layout
- Easy to replace with real components in subsequent WPs
