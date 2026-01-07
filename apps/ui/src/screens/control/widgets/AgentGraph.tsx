import { useEffect, useMemo, useRef, useState, type PointerEvent } from 'react'

import type { SessionEvent } from '../../../api/controlClient'
import './AgentGraph.css'

type GraphStatus = 'idle' | 'active' | 'complete' | 'failed'

type GraphNode = {
  id: string
  label: string
  role: string
  status: GraphStatus
}

type GraphEdge = {
  source: string
  target: string
  taskId?: string
}

interface AgentGraphProps {
  events: SessionEvent[]
}

const ROLE_COLORS: Record<GraphStatus, string> = {
  idle: '#cfd8dc',
  active: '#0ea5e9',
  complete: '#22c55e',
  failed: '#ef4444',
}

const DEFAULT_NODES: GraphNode[] = [
  { id: 'orchestrator', label: 'Orchestrator', role: 'orchestrator', status: 'idle' },
  { id: 'taskmaster', label: 'TaskMaster', role: 'taskmaster', status: 'idle' },
  { id: 'distributor', label: 'Distributor', role: 'distributor', status: 'idle' },
  { id: 'worker', label: 'Worker', role: 'worker', status: 'idle' },
  { id: 'foreman', label: 'Foreman', role: 'foreman', status: 'idle' },
  { id: 'fixer', label: 'Fixer', role: 'fixer', status: 'idle' },
  { id: 'reviewer', label: 'Reviewer', role: 'reviewer', status: 'idle' },
]

function parseTimestamp(timestamp: string) {
  return new Date(timestamp).getTime()
}

export default function AgentGraph({ events }: AgentGraphProps) {
  const svgRef = useRef<SVGSVGElement | null>(null)
  const [draggingId, setDraggingId] = useState<string | null>(null)
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({})

  const { nodes, edges } = useMemo(() => {
    const nodeMap = new Map<string, GraphNode>()
    DEFAULT_NODES.forEach((node) => nodeMap.set(node.id, { ...node }))
    const edgeMap = new Map<string, GraphEdge>()

    const orderedEvents = [...events].sort(
      (a, b) => parseTimestamp(a.timestamp) - parseTimestamp(b.timestamp)
    )

    orderedEvents.forEach((event) => {
      const role = (event.metadata?.agent_role as string) || event.metadata?.role
      const nodeId = role || 'worker'

      if (!nodeMap.has(nodeId)) {
        nodeMap.set(nodeId, {
          id: nodeId,
          label: nodeId.replace(/_/g, ' '),
          role: nodeId,
          status: 'idle',
        })
      }

      const existing = nodeMap.get(nodeId)!
      const next: GraphNode = { ...existing }

      switch (event.event_type) {
        case 'agent_invoked':
        case 'task_started': {
          next.status = 'active'
          break
        }
        case 'task_completed': {
          next.status = 'complete'
          break
        }
        case 'agent_completed': {
          next.status = event.metadata?.success === false ? 'failed' : 'complete'
          break
        }
        case 'task_failed': {
          next.status = 'failed'
          break
        }
        default:
          break
      }

      nodeMap.set(nodeId, next)

      if (event.task_id && role) {
        if (!edgeMap.has(event.task_id)) {
          edgeMap.set(event.task_id, {
            source: 'orchestrator',
            target: role,
            taskId: event.task_id,
          })
        }
      }
    })

    return {
      nodes: Array.from(nodeMap.values()),
      edges: Array.from(edgeMap.values()),
    }
  }, [events])

  // Seed new node positions when nodes change
  useEffect(() => {
    setPositions((prev) => {
      const next = { ...prev }
      const width = 760
      const height = 420
      const radius = Math.min(width, height) / 2 - 60

      nodes.forEach((node, idx) => {
        if (!next[node.id]) {
          const angle = (idx / Math.max(nodes.length, 1)) * Math.PI * 2
          next[node.id] = {
            x: width / 2 + radius * Math.cos(angle),
            y: height / 2 + radius * Math.sin(angle),
          }
        }
      })

      // Remove stale nodes
      Object.keys(next).forEach((id) => {
        if (!nodes.find((node) => node.id === id)) {
          delete next[id]
        }
      })

      return next
    })
  }, [nodes])

  const handlePointerMove = (event: PointerEvent<SVGCircleElement>) => {
    if (!draggingId || !svgRef.current) return
    const rect = svgRef.current.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    setPositions((prev) => ({
      ...prev,
      [draggingId]: { x, y },
    }))
  }

  const handlePointerUp = (event: PointerEvent<SVGCircleElement>) => {
    if (draggingId) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
    setDraggingId(null)
  }

  const renderEdge = (edge: GraphEdge) => {
    const sourcePos = positions[edge.source] || { x: 380, y: 210 }
    const targetPos = positions[edge.target] || { x: 380, y: 210 }

    return (
      <g key={`${edge.source}-${edge.target}-${edge.taskId}`} className="graph-edge">
        <line
          x1={sourcePos.x}
          y1={sourcePos.y}
          x2={targetPos.x}
          y2={targetPos.y}
          markerEnd="url(#arrowhead)"
        />
        {edge.taskId && (
          <text
            x={(sourcePos.x + targetPos.x) / 2}
            y={(sourcePos.y + targetPos.y) / 2 - 6}
            className="edge-label"
          >
            {edge.taskId}
          </text>
        )}
      </g>
    )
  }

  return (
    <section className="agent-graph">
      <div className="widget-header">
        <div>
          <h2>Agent Relationship Graph</h2>
          <p>Drag nodes to explore task flow between agents.</p>
        </div>
        <div className="graph-legend">
          {Object.entries(ROLE_COLORS).map(([status, color]) => (
            <span key={status} className="legend-item">
              <span className="legend-swatch" style={{ background: color }} />
              <span className="legend-label">{status}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="graph-surface">
        <svg ref={svgRef} viewBox="0 0 760 420" role="img" aria-label="Agent relationship graph">
          <defs>
            <marker
              id="arrowhead"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#90a4ae" />
            </marker>
          </defs>

          <rect x="0" y="0" width="760" height="420" className="graph-bg" />

          <g>
            {edges.map((edge) => renderEdge(edge))}
            {nodes.map((node) => {
              const position = positions[node.id] || { x: 380, y: 210 }
              return (
                <g
                  key={node.id}
                  className="graph-node"
                  transform={`translate(${position.x}, ${position.y})`}
                >
                  <circle
                    r={22}
                    fill={ROLE_COLORS[node.status]}
                    stroke="#37474f"
                    strokeWidth={1}
                    onPointerDown={(event) => {
                      setDraggingId(node.id)
                      event.currentTarget.setPointerCapture(event.pointerId)
                    }}
                    onPointerMove={handlePointerMove}
                    onPointerUp={handlePointerUp}
                  />
                  <text className="node-label" y={4}>
                    {node.label}
                  </text>
                </g>
              )
            })}
          </g>
        </svg>

        {edges.length === 0 && (
          <div className="graph-empty">Waiting for task events to render edges.</div>
        )}
      </div>
    </section>
  )
}
