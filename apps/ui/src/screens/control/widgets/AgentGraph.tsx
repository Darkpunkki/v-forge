import { useEffect, useMemo, useRef, useState, type PointerEvent } from 'react'

import type { AgentConfig, AgentFlowEdge } from '../../../api/controlClient'
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
  bidirectional?: boolean
}

interface AgentGraphProps {
  agents: AgentConfig[]
  edges: AgentFlowEdge[]
}

const ROLE_COLORS: Record<GraphStatus, string> = {
  idle: '#cfd8dc',
  active: '#0ea5e9',
  complete: '#22c55e',
  failed: '#ef4444',
}

export default function AgentGraph({ agents, edges: flowEdges }: AgentGraphProps) {
  const svgRef = useRef<SVGSVGElement | null>(null)
  const [draggingId, setDraggingId] = useState<string | null>(null)
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({})

  const { nodes, edges: graphEdges } = useMemo(() => {
    const nodeMap = new Map<string, GraphNode>()
    agents.forEach((agent) => {
      const label = agent.display_name || agent.role || agent.agent_id
      nodeMap.set(agent.agent_id, {
        id: agent.agent_id,
        label,
        role: agent.role || agent.agent_id,
        status: 'idle',
      })
    })

    const graphEdges = flowEdges
      .filter((edge) => edge.from_agent && edge.to_agent)
      .map((edge) => ({
        source: edge.from_agent,
        target: edge.to_agent,
        bidirectional: edge.bidirectional,
      }))

    graphEdges.forEach((edge) => {
      if (!nodeMap.has(edge.source)) {
        nodeMap.set(edge.source, {
          id: edge.source,
          label: edge.source,
          role: edge.source,
          status: 'idle',
        })
      }
      if (!nodeMap.has(edge.target)) {
        nodeMap.set(edge.target, {
          id: edge.target,
          label: edge.target,
          role: edge.target,
          status: 'idle',
        })
      }
    })

    return {
      nodes: Array.from(nodeMap.values()),
      edges: graphEdges,
    }
  }, [agents, flowEdges])

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

  const renderEdge = (edge: GraphEdge, index: number) => {
    const sourcePos = positions[edge.source] || { x: 380, y: 210 }
    const targetPos = positions[edge.target] || { x: 380, y: 210 }

    return (
      <g key={`${edge.source}-${edge.target}-${index}`} className="graph-edge">
        <line
          x1={sourcePos.x}
          y1={sourcePos.y}
          x2={targetPos.x}
          y2={targetPos.y}
          markerStart={edge.bidirectional ? 'url(#arrowhead)' : undefined}
          markerEnd="url(#arrowhead)"
        />
      </g>
    )
  }

  return (
    <section className="agent-graph">
      <div className="widget-header">
        <div>
          <h2>Agent Communication Graph</h2>
          <p>Drag nodes to explore communication links between agents.</p>
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
            {graphEdges.map((edge, index) => renderEdge(edge, index))}
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

        {graphEdges.length === 0 && (
          <div className="graph-empty">Configure communication graph.</div>
        )}
      </div>
    </section>
  )
}
