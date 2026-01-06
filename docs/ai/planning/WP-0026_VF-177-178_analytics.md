# WP-0026 — Analytics (Comparison + Events)

## VF Tasks Included
- [ ] VF-177 — Session comparison view (multi-session metrics)
  - **Files:**
    - `apps/ui/src/screens/control/widgets/SessionComparison.tsx` (comparison view)
    - `apps/ui/src/screens/control/widgets/SessionComparison.css` (styling)
  - **Tests:**
    - `apps/ui/src/screens/control/widgets/__tests__/SessionComparison.test.tsx` (component tests)
  - **Verify:** Comparison table shows metrics for multiple sessions, sortable columns

- [ ] VF-178 — Event stream viewer (real-time log with filtering)
  - **Files:**
    - `apps/ui/src/screens/control/widgets/EventStream.tsx` (live event feed)
    - `apps/ui/src/screens/control/widgets/EventStream.css` (styling)
  - **Tests:**
    - `apps/ui/src/screens/control/widgets/__tests__/EventStream.test.tsx` (component tests)
  - **Verify:** Event stream shows real-time events, filters by event type, search works

## Goal
Enable A/B testing of different agent configurations, model selections, and gate policies by comparing session metrics side-by-side. Provide raw event stream access for debugging and audit trails.

## Dependencies
- ✅ WP-0021 (EventLog + structured events) - provides event data and session queries
- ✅ WP-0022 (Control panel architecture) - provides widget container and SSE infrastructure

## Why Critical
Without comparison views, developers can't answer questions like:
- "Does using gpt-4o instead of gpt-4o-mini improve success rate?"
- "How much faster is the new gate policy?"
- "Which agent configuration is most cost-efficient?"

Event stream provides raw data access for debugging edge cases.

## Execution Steps

### 1. Session Comparison Widget

**Intent:** Side-by-side comparison of session metrics for A/B testing.

**Implementation:**

Create `apps/ui/src/screens/control/widgets/SessionComparison.tsx`:
```tsx
import React, { useEffect, useState } from 'react';
import { controlClient } from '../../../api/controlClient';
import './SessionComparison.css';

interface SessionMetrics {
  sessionId: string;
  createdAt: Date;
  phase: string;
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  totalTokens: number;
  totalCost: number;
  duration: number; // seconds
  avgTaskDuration: number; // seconds
  escalationCount: number;
  gateBlockCount: number;
}

interface SessionComparisonProps {
  sessionIds: string[];
}

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  'gpt-4o': { prompt: 2.5, completion: 10.0 },
  'gpt-4o-mini': { prompt: 0.15, completion: 0.6 },
  'claude-sonnet-4': { prompt: 3.0, completion: 15.0 },
  'claude-opus-4': { prompt: 15.0, completion: 75.0 },
};

const SessionComparison: React.FC<SessionComparisonProps> = ({ sessionIds }) => {
  const [metrics, setMetrics] = useState<SessionMetrics[]>([]);
  const [sortBy, setSortBy] = useState<keyof SessionMetrics>('createdAt');
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, [sessionIds]);

  const loadMetrics = async () => {
    const metricsPromises = sessionIds.map(async (sessionId) => {
      try {
        const status = await controlClient.getSessionStatus(sessionId);
        const events = await fetchAllEvents(sessionId);

        return calculateMetrics(sessionId, status, events);
      } catch (error) {
        console.error(`Failed to load metrics for ${sessionId}:`, error);
        return null;
      }
    });

    const results = await Promise.all(metricsPromises);
    setMetrics(results.filter((m) => m !== null) as SessionMetrics[]);
  };

  const fetchAllEvents = async (sessionId: string): Promise<any[]> => {
    // Note: In production, this should use the API endpoint
    // For now, we'll use SSE to collect events (simplified)
    return new Promise((resolve) => {
      const events: any[] = [];
      const eventSource = controlClient.streamSessionEvents(sessionId, (event) => {
        events.push(event);
      });

      // Close after 2 seconds (all historical events should be received)
      setTimeout(() => {
        eventSource.close();
        resolve(events);
      }, 2000);
    });
  };

  const calculateMetrics = (sessionId: string, status: any, events: any[]): SessionMetrics => {
    const createdAt = new Date(status.created_at);
    const updatedAt = new Date(status.updated_at);
    const duration = (updatedAt.getTime() - createdAt.getTime()) / 1000;

    // Count tokens and calculate cost
    let totalTokens = 0;
    let totalCost = 0;
    events
      .filter((e) => e.event_type === 'LLM_RESPONSE_RECEIVED')
      .forEach((e) => {
        const tokens = e.metadata?.total_tokens || 0;
        const model = e.model || 'gpt-4o-mini';
        const promptTokens = e.metadata?.prompt_tokens || 0;
        const completionTokens = e.metadata?.completion_tokens || 0;

        totalTokens += tokens;

        const pricing = MODEL_PRICING[model] || { prompt: 1.0, completion: 2.0 };
        totalCost += (promptTokens / 1_000_000) * pricing.prompt;
        totalCost += (completionTokens / 1_000_000) * pricing.completion;
      });

    // Count escalations
    const escalationCount = events.filter(
      (e) => e.event_type === 'AGENT_INVOKED' && (e.metadata?.failure_count || 0) > 0
    ).length;

    // Count gate blocks
    const gateBlockCount = events.filter(
      (e) => e.event_type === 'GATE_EVALUATED' && e.metadata?.status === 'BLOCK'
    ).length;

    // Calculate avg task duration
    const taskDurations: number[] = [];
    const taskStartTimes: Record<string, number> = {};
    events.forEach((e) => {
      if (e.event_type === 'TASK_STARTED' && e.task_id) {
        taskStartTimes[e.task_id] = new Date(e.timestamp).getTime();
      }
      if (e.event_type === 'TASK_COMPLETED' && e.task_id && taskStartTimes[e.task_id]) {
        const duration = (new Date(e.timestamp).getTime() - taskStartTimes[e.task_id]) / 1000;
        taskDurations.push(duration);
      }
    });

    const avgTaskDuration =
      taskDurations.length > 0
        ? taskDurations.reduce((sum, d) => sum + d, 0) / taskDurations.length
        : 0;

    return {
      sessionId,
      createdAt,
      phase: status.phase,
      totalTasks: status.completed_tasks + status.failed_tasks + (status.active_task_id ? 1 : 0),
      completedTasks: status.completed_tasks,
      failedTasks: status.failed_tasks,
      totalTokens,
      totalCost,
      duration,
      avgTaskDuration,
      escalationCount,
      gateBlockCount,
    };
  };

  const handleSort = (column: keyof SessionMetrics) => {
    if (sortBy === column) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(column);
      setSortDesc(true);
    }
  };

  const sortedMetrics = [...metrics].sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];

    if (aVal < bVal) return sortDesc ? 1 : -1;
    if (aVal > bVal) return sortDesc ? -1 : 1;
    return 0;
  });

  const getSortIcon = (column: keyof SessionMetrics) => {
    if (sortBy !== column) return '⇅';
    return sortDesc ? '↓' : '↑';
  };

  return (
    <div className="session-comparison-widget">
      <h3>Session Comparison</h3>

      {metrics.length === 0 ? (
        <div className="no-data">No sessions to compare</div>
      ) : (
        <div className="comparison-table-container">
          <table className="comparison-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('sessionId')}>
                  Session ID {getSortIcon('sessionId')}
                </th>
                <th onClick={() => handleSort('phase')}>
                  Phase {getSortIcon('phase')}
                </th>
                <th onClick={() => handleSort('completedTasks')}>
                  Tasks {getSortIcon('completedTasks')}
                </th>
                <th onClick={() => handleSort('totalTokens')}>
                  Tokens {getSortIcon('totalTokens')}
                </th>
                <th onClick={() => handleSort('totalCost')}>
                  Cost {getSortIcon('totalCost')}
                </th>
                <th onClick={() => handleSort('duration')}>
                  Duration {getSortIcon('duration')}
                </th>
                <th onClick={() => handleSort('avgTaskDuration')}>
                  Avg Task {getSortIcon('avgTaskDuration')}
                </th>
                <th onClick={() => handleSort('escalationCount')}>
                  Escalations {getSortIcon('escalationCount')}
                </th>
                <th onClick={() => handleSort('gateBlockCount')}>
                  Blocks {getSortIcon('gateBlockCount')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedMetrics.map((session) => (
                <tr key={session.sessionId}>
                  <td className="session-id">
                    {session.sessionId.substring(0, 8)}
                  </td>
                  <td className={`phase ${session.phase.toLowerCase()}`}>
                    {session.phase}
                  </td>
                  <td>
                    <span className="completed">{session.completedTasks}</span>/
                    <span className="total">{session.totalTasks}</span>
                    {session.failedTasks > 0 && (
                      <span className="failed"> ({session.failedTasks} failed)</span>
                    )}
                  </td>
                  <td className="numeric">{session.totalTokens.toLocaleString()}</td>
                  <td className="numeric">${session.totalCost.toFixed(4)}</td>
                  <td className="numeric">{session.duration.toFixed(0)}s</td>
                  <td className="numeric">{session.avgTaskDuration.toFixed(1)}s</td>
                  <td className="numeric">
                    {session.escalationCount > 0 ? (
                      <span className="escalation">{session.escalationCount}</span>
                    ) : (
                      0
                    )}
                  </td>
                  <td className="numeric">
                    {session.gateBlockCount > 0 ? (
                      <span className="blocked">{session.gateBlockCount}</span>
                    ) : (
                      0
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default SessionComparison;
```

Create `apps/ui/src/screens/control/widgets/SessionComparison.css`:
```css
.session-comparison-widget {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  height: 500px;
  display: flex;
  flex-direction: column;
}

.session-comparison-widget h3 {
  margin: 0 0 1rem 0;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.no-data {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #777;
}

.comparison-table-container {
  flex: 1;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 1rem;
  overflow: auto;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.comparison-table th {
  background-color: #3a3a3a;
  color: #aaa;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  position: sticky;
  top: 0;
  z-index: 1;
}

.comparison-table th:hover {
  background-color: #4a4a4a;
}

.comparison-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #3a3a3a;
  color: #e0e0e0;
}

.comparison-table tr:hover {
  background-color: #2d2d2d;
}

.session-id {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  color: #667eea;
}

.phase {
  text-transform: uppercase;
  font-weight: 600;
  font-size: 0.8rem;
}

.phase.complete {
  color: #10b981;
}

.phase.failed {
  color: #ef4444;
}

.phase.execution {
  color: #f59e0b;
}

.completed {
  color: #10b981;
  font-weight: 600;
}

.failed {
  color: #ef4444;
  font-weight: 600;
}

.total {
  color: #aaa;
}

.numeric {
  text-align: right;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.escalation {
  color: #f59e0b;
  font-weight: 600;
}

.blocked {
  color: #ef4444;
  font-weight: 600;
}
```

---

### 2. Event Stream Viewer Widget

**Intent:** Real-time event feed with filtering and search for debugging.

**Implementation:**

Create `apps/ui/src/screens/control/widgets/EventStream.tsx`:
```tsx
import React, { useEffect, useState, useRef } from 'react';
import { controlClient, SessionEvent } from '../../../api/controlClient';
import './EventStream.css';

interface EventStreamProps {
  sessionId: string;
}

const EventStream: React.FC<EventStreamProps> = ({ sessionId }) => {
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState(true);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const eventSource = controlClient.streamSessionEvents(sessionId, handleEvent);
    return () => eventSource.close();
  }, [sessionId]);

  const handleEvent = (event: SessionEvent) => {
    setEvents((prev) => [...prev, event]); // Append (chronological order)
  };

  useEffect(() => {
    if (autoScroll && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  const eventTypes = [
    'ALL',
    'PHASE_TRANSITION',
    'TASK_STARTED',
    'TASK_COMPLETED',
    'TASK_FAILED',
    'AGENT_INVOKED',
    'LLM_REQUEST_SENT',
    'LLM_RESPONSE_RECEIVED',
    'GATE_EVALUATED',
    'PATCH_APPLIED',
    'VERIFICATION_RUN',
  ];

  const filteredEvents = events.filter((event) => {
    // Filter by type
    if (filterType !== 'ALL' && event.event_type !== filterType) {
      return false;
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchMessage = event.message.toLowerCase().includes(query);
      const matchTaskId = event.task_id?.toLowerCase().includes(query);
      const matchMetadata = JSON.stringify(event.metadata || {})
        .toLowerCase()
        .includes(query);

      return matchMessage || matchTaskId || matchMetadata;
    }

    return true;
  });

  const getEventTypeClass = (eventType: string): string => {
    if (eventType.includes('FAILED') || eventType.includes('BLOCK')) return 'error';
    if (eventType.includes('COMPLETED') || eventType.includes('PASS')) return 'success';
    if (eventType.includes('STARTED') || eventType.includes('INVOKED')) return 'info';
    if (eventType.includes('WARN')) return 'warning';
    return 'default';
  };

  return (
    <div className="event-stream-widget">
      <div className="stream-header">
        <h3>Event Stream</h3>
        <div className="stream-controls">
          <select
            className="type-filter"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            {eventTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>

          <input
            className="search-input"
            type="text"
            placeholder="Search events..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <label className="autoscroll-toggle">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>

          <button
            className="clear-button"
            onClick={() => setEvents([])}
            title="Clear event log"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="event-log" ref={logRef}>
        {filteredEvents.length === 0 ? (
          <div className="no-events">
            {events.length === 0
              ? 'Waiting for events...'
              : 'No events match the current filters'}
          </div>
        ) : (
          <ul className="event-list">
            {filteredEvents.map((event, idx) => (
              <li key={idx} className={`event-item ${getEventTypeClass(event.event_type)}`}>
                <div className="event-time">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
                <div className="event-type">{event.event_type}</div>
                <div className="event-message">{event.message}</div>
                {event.task_id && (
                  <div className="event-task">Task: {event.task_id.substring(0, 8)}</div>
                )}
                {event.agent_role && (
                  <div className="event-agent">Agent: {event.agent_role}</div>
                )}
                {event.metadata && Object.keys(event.metadata).length > 0 && (
                  <details className="event-metadata">
                    <summary>Metadata</summary>
                    <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
                  </details>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="stream-footer">
        <span className="event-count">
          Showing {filteredEvents.length} of {events.length} events
        </span>
      </div>
    </div>
  );
};

export default EventStream;
```

Create `apps/ui/src/screens/control/widgets/EventStream.css`:
```css
.event-stream-widget {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  height: 700px;
  display: flex;
  flex-direction: column;
}

.stream-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.stream-header h3 {
  margin: 0;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.stream-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.type-filter,
.search-input {
  padding: 0.5rem;
  background-color: #3a3a3a;
  color: #e0e0e0;
  border: 1px solid #555;
  border-radius: 4px;
  font-size: 0.85rem;
}

.type-filter {
  width: 200px;
}

.search-input {
  width: 250px;
}

.autoscroll-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #aaa;
  cursor: pointer;
}

.clear-button {
  padding: 0.5rem 1rem;
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background-color 0.2s;
}

.clear-button:hover {
  background-color: #dc2626;
}

.event-log {
  flex: 1;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 1rem;
  overflow-y: auto;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 0.85rem;
}

.no-events {
  text-align: center;
  padding: 2rem;
  color: #777;
}

.event-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.event-item {
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background-color: #2d2d2d;
  border-radius: 4px;
  border-left: 4px solid #6b7280;
}

.event-item.error {
  border-left-color: #ef4444;
}

.event-item.success {
  border-left-color: #10b981;
}

.event-item.info {
  border-left-color: #667eea;
}

.event-item.warning {
  border-left-color: #f59e0b;
}

.event-time {
  color: #777;
  font-size: 0.8rem;
  margin-bottom: 0.25rem;
}

.event-type {
  color: #667eea;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.event-message {
  color: #e0e0e0;
  margin-bottom: 0.5rem;
}

.event-task,
.event-agent {
  color: #aaa;
  font-size: 0.8rem;
  margin-bottom: 0.25rem;
}

.event-metadata {
  margin-top: 0.5rem;
  cursor: pointer;
}

.event-metadata summary {
  color: #667eea;
  font-size: 0.8rem;
  user-select: none;
}

.event-metadata pre {
  background-color: #1e1e1e;
  padding: 0.5rem;
  border-radius: 4px;
  margin-top: 0.5rem;
  overflow-x: auto;
  color: #10b981;
  font-size: 0.75rem;
}

.stream-footer {
  margin-top: 1rem;
  text-align: center;
  color: #777;
  font-size: 0.85rem;
}
```

---

### 3. Integrate Widgets into ControlPanel

**Intent:** Add analytics widgets to control panel layout.

**Implementation:**

Update `apps/ui/src/screens/control/ControlPanel.tsx`:
```tsx
import SessionComparison from './widgets/SessionComparison';
import EventStream from './widgets/EventStream';

// Inside the widgets-grid:
<div className="widgets-grid">
  {/* WP-0023 widgets */}
  <AgentDashboard sessionId={selectedSession} />
  <TokenVisualization sessionId={selectedSession} />

  {/* WP-0024 widgets */}
  <AgentGraph sessionId={selectedSession} />
  <ExecutionTimeline sessionId={selectedSession} />

  {/* WP-0025 widgets */}
  <GateLog sessionId={selectedSession} />
  <ModelRouter sessionId={selectedSession} />

  {/* WP-0026 widgets (NEW) */}
  <SessionComparison sessionIds={[selectedSession]} />
  <EventStream sessionId={selectedSession} />

  {/* WP-0027 placeholders */}
  <div className="widget-slot">🔍 Prompt Inspector (WP-0027)</div>
  <div className="widget-slot">💵 Cost Analytics (WP-0027)</div>
</div>
```

---

## Verification Commands
```bash
# Frontend build
cd apps/ui && npm run build

# Frontend dev server
cd apps/ui && npm run dev
# Visit: http://localhost:5173/control

# Test session comparison:
# 1. Run multiple sessions with different configurations
# 2. Navigate to /control
# 3. Verify SessionComparison shows metrics for all sessions
# 4. Verify sorting by clicking column headers
# 5. Verify cost and token calculations

# Test event stream:
# 1. Select an active session
# 2. Verify EventStream shows real-time events
# 3. Test filtering by event type
# 4. Test search functionality
# 5. Verify auto-scroll and clear buttons work
```

## Done Means
- [ ] SessionComparison component renders comparison table
- [ ] SessionComparison calculates token usage, cost, duration from events
- [ ] SessionComparison supports sorting by any column
- [ ] SessionComparison highlights escalations and gate blocks
- [ ] EventStream component renders real-time event feed
- [ ] EventStream filters by event type dropdown
- [ ] EventStream supports text search across message/task/metadata
- [ ] EventStream supports auto-scroll toggle
- [ ] EventStream supports clear button
- [ ] EventStream displays metadata in collapsible sections
- [ ] Both widgets integrate into ControlPanel layout

## Architecture Notes

**Session Comparison Design:**
- Fetches all events for each session to calculate metrics
- Uses Promise.all for parallel session loading
- Calculates cost using model-specific pricing
- Tracks escalation count (AGENT_INVOKED with failure_count > 0)
- Tracks gate block count (GATE_EVALUATED with status=BLOCK)

**Metric Calculations:**
- Duration: updated_at - created_at
- Avg task duration: (sum of task durations) / task count
- Total tokens: sum of LLM_RESPONSE_RECEIVED metadata.total_tokens
- Total cost: sum of (prompt_tokens × prompt_price + completion_tokens × completion_price)

**Event Stream Design:**
- Auto-scroll by default (useful for live monitoring)
- Search across message, task_id, and metadata (full-text)
- Color-coded border (red=error, green=success, blue=info, orange=warning)
- Collapsible metadata for detailed inspection
- Clear button for long-running sessions

**Event Type Classification:**
- Error: FAILED, BLOCK
- Success: COMPLETED, PASS
- Info: STARTED, INVOKED
- Warning: WARN

**Why These Widgets Matter:**
- **SessionComparison** - Enables A/B testing of agent configurations
- **EventStream** - Provides raw data access for debugging edge cases
- Together they support both high-level analysis and deep debugging
