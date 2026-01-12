# WP-0024 — Execution Visualization (Graph + Timeline)

## VF Tasks Included
- [x] VF-173 — Agent relationship graph (interactive DAG visualization)
  - **Notes:**
    - Built `AgentGraph` as a drag-friendly SVG graph that listens to session events for node status and edges.
    - Added dedicated styling and legend plus ControlPanel integration alongside existing widgets.
    - Used dependency-free SVG layout due to npm registry restrictions on fetching d3 packages (403 in this environment).

- [x] VF-174 — Execution flow timeline (Gantt-style with agent swim lanes)
  - **Notes:**
    - Implemented `ExecutionTimeline` with per-agent swim lanes, duration-based bars, and status colors.
    - Bars derive from task start/complete/fail events with automatic duration scaling.
    - Integrated into ControlPanel grid next to the agent dashboard and token visualizations.

## Goal
Provide visual understanding of agent coordination patterns and execution flow to help developers identify bottlenecks, understand task dependencies, and optimize agent allocation.

## Dependencies
- ✅ WP-0021 (EventLog + structured events) - provides task timing data
- ✅ WP-0022 (Control panel architecture) - provides widget container and SSE infrastructure
- ✅ WP-0023 (Agent dashboard) - provides agent status data

## Why Critical
These visualizations transform raw event streams into actionable insights. Without them, developers must parse logs manually to understand agent coordination and execution patterns.

## Execution Steps

### 1. Agent Relationship Graph (D3.js)

**Intent:** Visualize task flow and agent coordination as an interactive directed graph.

**Implementation:**

Install D3.js dependency:
```bash
cd apps/ui && npm install d3 @types/d3
```

Create `apps/ui/src/screens/control/widgets/AgentGraph.tsx`:
```tsx
import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { controlClient, SessionEvent } from '../../../api/controlClient';
import './AgentGraph.css';

interface GraphNode {
  id: string;
  label: string;
  role: string;
  status: 'idle' | 'active' | 'complete' | 'failed';
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphEdge {
  source: string;
  target: string;
  taskId: string;
}

interface AgentGraphProps {
  sessionId: string;
}

const AgentGraph: React.FC<AgentGraphProps> = ({ sessionId }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([
    { id: 'orchestrator', label: 'Orchestrator', role: 'orchestrator', status: 'idle' },
    { id: 'worker', label: 'Worker', role: 'worker', status: 'idle' },
    { id: 'foreman', label: 'Foreman', role: 'foreman', status: 'idle' },
    { id: 'fixer', label: 'Fixer', role: 'fixer', status: 'idle' },
  ]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);

  useEffect(() => {
    const eventSource = controlClient.streamSessionEvents(sessionId, handleEvent);
    return () => eventSource.close();
  }, [sessionId]);

  const handleEvent = (event: SessionEvent) => {
    if (event.event_type === 'AGENT_INVOKED' && event.agent_role) {
      // Update node status
      setNodes((prev) =>
        prev.map((node) =>
          node.id === event.agent_role
            ? { ...node, status: 'active' }
            : node
        )
      );
    }

    if (event.event_type === 'TASK_COMPLETED' && event.agent_role && event.task_id) {
      // Add edge from orchestrator to executing agent
      setEdges((prev) => [
        ...prev,
        {
          source: 'orchestrator',
          target: event.agent_role,
          taskId: event.task_id,
        },
      ]);

      // Mark node as complete
      setNodes((prev) =>
        prev.map((node) =>
          node.id === event.agent_role
            ? { ...node, status: 'complete' }
            : node
        )
      );
    }

    if (event.event_type === 'TASK_FAILED' && event.agent_role) {
      // Mark node as failed
      setNodes((prev) =>
        prev.map((node) =>
          node.id === event.agent_role
            ? { ...node, status: 'failed' }
            : node
        )
      );
    }
  };

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = 800;
    const height = 600;

    svg.attr('width', width).attr('height', height);

    // Clear previous render
    svg.selectAll('*').remove();

    // Create simulation
    const simulation = d3
      .forceSimulation<GraphNode>(nodes)
      .force(
        'link',
        d3
          .forceLink<GraphNode, GraphEdge>(edges)
          .id((d) => d.id)
          .distance(150)
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(60));

    // Draw edges
    const link = svg
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(edges)
      .enter()
      .append('line')
      .attr('class', 'edge')
      .attr('stroke', '#667eea')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)');

    // Define arrowhead marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#667eea');

    // Draw nodes
    const node = svg
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .call(
        d3
          .drag<SVGGElement, GraphNode>()
          .on('start', dragStarted)
          .on('drag', dragged)
          .on('end', dragEnded)
      );

    // Node circles
    node
      .append('circle')
      .attr('r', 30)
      .attr('class', (d) => `node-circle ${d.status}`)
      .attr('fill', (d) => {
        if (d.status === 'active') return '#f59e0b';
        if (d.status === 'complete') return '#10b981';
        if (d.status === 'failed') return '#ef4444';
        return '#6b7280';
      });

    // Node labels
    node
      .append('text')
      .attr('dy', 4)
      .attr('text-anchor', 'middle')
      .attr('class', 'node-label')
      .text((d) => d.label);

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as GraphNode).x || 0)
        .attr('y1', (d) => (d.source as GraphNode).y || 0)
        .attr('x2', (d) => (d.target as GraphNode).x || 0)
        .attr('y2', (d) => (d.target as GraphNode).y || 0);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    function dragStarted(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }, [nodes, edges]);

  return (
    <div className="agent-graph-widget">
      <h3>Agent Relationship Graph</h3>
      <svg ref={svgRef} className="graph-svg"></svg>
      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-color idle"></span> Idle
        </div>
        <div className="legend-item">
          <span className="legend-color active"></span> Active
        </div>
        <div className="legend-item">
          <span className="legend-color complete"></span> Complete
        </div>
        <div className="legend-item">
          <span className="legend-color failed"></span> Failed
        </div>
      </div>
    </div>
  );
};

export default AgentGraph;
```

Create `apps/ui/src/screens/control/widgets/AgentGraph.css`:
```css
.agent-graph-widget {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  height: 700px;
  display: flex;
  flex-direction: column;
}

.agent-graph-widget h3 {
  margin: 0 0 1rem 0;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.graph-svg {
  flex: 1;
  background-color: #1e1e1e;
  border-radius: 4px;
}

.node-label {
  fill: #e0e0e0;
  font-size: 12px;
  pointer-events: none;
}

.node-circle {
  stroke: #1e1e1e;
  stroke-width: 2px;
  cursor: grab;
}

.node-circle:active {
  cursor: grabbing;
}

.edge {
  opacity: 0.6;
}

.graph-legend {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #aaa;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #1e1e1e;
}

.legend-color.idle {
  background-color: #6b7280;
}

.legend-color.active {
  background-color: #f59e0b;
}

.legend-color.complete {
  background-color: #10b981;
}

.legend-color.failed {
  background-color: #ef4444;
}
```

---

### 2. Execution Flow Timeline (Gantt-style)

**Intent:** Show task execution timing with horizontal swim lanes per agent role.

**Implementation:**

Create `apps/ui/src/screens/control/widgets/ExecutionTimeline.tsx`:
```tsx
import React, { useEffect, useState } from 'react';
import { controlClient, SessionEvent } from '../../../api/controlClient';
import './ExecutionTimeline.css';

interface TimelineTask {
  taskId: string;
  agentRole: string;
  startTime: Date;
  endTime: Date | null;
  status: 'running' | 'complete' | 'failed';
  description: string;
}

interface ExecutionTimelineProps {
  sessionId: string;
}

const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({ sessionId }) => {
  const [tasks, setTasks] = useState<TimelineTask[]>([]);
  const [sessionStartTime, setSessionStartTime] = useState<Date>(new Date());

  const agentRoles = ['orchestrator', 'worker', 'foreman', 'fixer'];

  useEffect(() => {
    const eventSource = controlClient.streamSessionEvents(sessionId, handleEvent);
    return () => eventSource.close();
  }, [sessionId]);

  const handleEvent = (event: SessionEvent) => {
    if (event.event_type === 'PHASE_TRANSITION' && event.phase === 'EXECUTION') {
      setSessionStartTime(new Date(event.timestamp));
    }

    if (event.event_type === 'TASK_STARTED' && event.task_id && event.agent_role) {
      setTasks((prev) => [
        ...prev,
        {
          taskId: event.task_id,
          agentRole: event.agent_role,
          startTime: new Date(event.timestamp),
          endTime: null,
          status: 'running',
          description: event.message,
        },
      ]);
    }

    if (event.event_type === 'TASK_COMPLETED' && event.task_id) {
      setTasks((prev) =>
        prev.map((task) =>
          task.taskId === event.task_id
            ? {
                ...task,
                endTime: new Date(event.timestamp),
                status: 'complete',
              }
            : task
        )
      );
    }

    if (event.event_type === 'TASK_FAILED' && event.task_id) {
      setTasks((prev) =>
        prev.map((task) =>
          task.taskId === event.task_id
            ? {
                ...task,
                endTime: new Date(event.timestamp),
                status: 'failed',
              }
            : task
        )
      );
    }
  };

  // Calculate timeline dimensions
  const now = new Date();
  const totalDuration = (now.getTime() - sessionStartTime.getTime()) / 1000; // seconds
  const timelineWidth = 1000; // pixels

  const getTaskPosition = (task: TimelineTask) => {
    const startOffset = (task.startTime.getTime() - sessionStartTime.getTime()) / 1000;
    const left = (startOffset / totalDuration) * timelineWidth;

    const endTime = task.endTime || now;
    const duration = (endTime.getTime() - task.startTime.getTime()) / 1000;
    const width = (duration / totalDuration) * timelineWidth;

    return { left, width };
  };

  return (
    <div className="execution-timeline-widget">
      <h3>Execution Timeline</h3>

      <div className="timeline-container">
        {/* Time axis */}
        <div className="time-axis">
          <div className="time-label">0s</div>
          <div className="time-label">{(totalDuration / 4).toFixed(0)}s</div>
          <div className="time-label">{(totalDuration / 2).toFixed(0)}s</div>
          <div className="time-label">{((3 * totalDuration) / 4).toFixed(0)}s</div>
          <div className="time-label">{totalDuration.toFixed(0)}s</div>
        </div>

        {/* Swim lanes */}
        {agentRoles.map((role) => (
          <div key={role} className="swim-lane">
            <div className="lane-label">{role}</div>
            <div className="lane-track">
              {tasks
                .filter((task) => task.agentRole === role)
                .map((task) => {
                  const { left, width } = getTaskPosition(task);
                  return (
                    <div
                      key={task.taskId}
                      className={`task-bar ${task.status}`}
                      style={{
                        left: `${left}px`,
                        width: `${Math.max(width, 20)}px`,
                      }}
                      title={`${task.taskId}: ${task.description}`}
                    >
                      <span className="task-label">{task.taskId.substring(0, 6)}</span>
                    </div>
                  );
                })}
            </div>
          </div>
        ))}
      </div>

      <div className="timeline-legend">
        <div className="legend-item">
          <span className="bar running"></span> Running
        </div>
        <div className="legend-item">
          <span className="bar complete"></span> Complete
        </div>
        <div className="legend-item">
          <span className="bar failed"></span> Failed
        </div>
      </div>
    </div>
  );
};

export default ExecutionTimeline;
```

Create `apps/ui/src/screens/control/widgets/ExecutionTimeline.css`:
```css
.execution-timeline-widget {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  height: 500px;
  display: flex;
  flex-direction: column;
}

.execution-timeline-widget h3 {
  margin: 0 0 1rem 0;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.timeline-container {
  flex: 1;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 1rem;
  overflow-x: auto;
}

.time-axis {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding: 0 120px 0 0; /* Offset for lane labels */
}

.time-label {
  font-size: 0.8rem;
  color: #777;
}

.swim-lane {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  position: relative;
}

.lane-label {
  width: 100px;
  font-size: 0.9rem;
  color: #aaa;
  font-weight: 600;
  text-transform: capitalize;
}

.lane-track {
  flex: 1;
  height: 40px;
  background-color: #2d2d2d;
  border-radius: 4px;
  position: relative;
}

.task-bar {
  position: absolute;
  height: 30px;
  top: 5px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  padding: 0 0.5rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.task-bar:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.task-bar.running {
  background: linear-gradient(90deg, #f59e0b, #fb923c);
  border: 1px solid #f59e0b;
}

.task-bar.complete {
  background: linear-gradient(90deg, #10b981, #34d399);
  border: 1px solid #10b981;
}

.task-bar.failed {
  background: linear-gradient(90deg, #ef4444, #f87171);
  border: 1px solid #ef4444;
}

.task-label {
  font-size: 0.75rem;
  color: white;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.timeline-legend {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  justify-content: center;
}

.timeline-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #aaa;
}

.timeline-legend .bar {
  width: 40px;
  height: 16px;
  border-radius: 4px;
}

.timeline-legend .bar.running {
  background: linear-gradient(90deg, #f59e0b, #fb923c);
}

.timeline-legend .bar.complete {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.timeline-legend .bar.failed {
  background: linear-gradient(90deg, #ef4444, #f87171);
}
```

---

### 3. Integrate Widgets into ControlPanel

**Intent:** Replace placeholder slots with real components.

**Implementation:**

Update `apps/ui/src/screens/control/ControlPanel.tsx`:
```tsx
import AgentGraph from './widgets/AgentGraph';
import ExecutionTimeline from './widgets/ExecutionTimeline';

// Inside the control-content main section:
{selectedSession ? (
  <div className="session-details">
    <h2>Session: {selectedSession.substring(0, 8)}</h2>

    <div className="widgets-grid">
      {/* WP-0023 widgets */}
      <AgentDashboard sessionId={selectedSession} />
      <TokenVisualization sessionId={selectedSession} />

      {/* WP-0024 widgets (NEW) */}
      <AgentGraph sessionId={selectedSession} />
      <ExecutionTimeline sessionId={selectedSession} />

      {/* WP-0025-0027 placeholders */}
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
```

---

## Verification Commands
```bash
# Frontend build (pass)
cd apps/ui && npm run build

# Manual check
# - Connect to /control while a session is running
# - Confirm graph nodes change status as events stream in and edges appear per task
# - Confirm timeline shows per-agent bars with running/complete/failed colors
```

## Done Means
- [x] AgentGraph component renders interactive SVG graph
- [x] Graph nodes represent agents (orchestrator, worker, foreman, fixer)
- [x] Graph edges represent task flow (orchestrator → executing agent)
- [x] Graph nodes update color based on agent status (idle/active/complete/failed)
- [x] Graph supports drag-to-reposition nodes
- [x] ExecutionTimeline component renders Gantt-style timeline
- [x] Timeline shows swim lanes for each agent role
- [x] Timeline shows task bars with start/end times
- [x] Timeline updates in real-time via SSE events
- [x] Both widgets integrate into ControlPanel layout
- [x] Build passes without additional dependencies (d3 unavailable in offline registry)

## Architecture Notes

**Why D3.js for Agent Graph:**
- Industry standard for complex data visualizations
- Force simulation provides automatic layout
- Supports drag, zoom, pan interactions
- Can scale to 100+ nodes if needed

**Force Simulation Parameters:**
- `distance(150)` - keeps nodes well-spaced
- `strength(-400)` - prevents node clustering
- `collision(60)` - prevents overlapping nodes

**Timeline Time Calculation:**
- Uses session start time as t=0
- Calculates task positions relative to session duration
- Auto-scales timeline width to fit all tasks
- Updates every second via SSE polling

**Gantt Chart Design:**
- Horizontal swim lanes match common PM tools (Jira, Asana)
- Color coding: orange (running), green (complete), red (failed)
- Gradient fills add visual polish
- Hover tooltips show full task details

**Event Dependencies:**
- PHASE_TRANSITION (EXECUTION) → set session start time
- TASK_STARTED → create timeline bar
- TASK_COMPLETED/FAILED → update bar color and end time
- AGENT_INVOKED → update graph node status

**Scalability Considerations:**
- Graph limited to 4 agent roles (manageable for force simulation)
- Timeline auto-scrolls horizontally for long sessions
- Can add time window filtering if sessions exceed 1 hour
