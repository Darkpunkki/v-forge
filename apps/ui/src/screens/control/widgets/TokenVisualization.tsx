import { useMemo } from 'react'

import type { SessionEvent } from '../../../api/controlClient'

type TokenEvent = {
  role: string
  model?: string
  promptTokens: number
  completionTokens: number
  totalTokens: number
  timestamp: Date
}

const ROLE_COLORS = ['#1976d2', '#9c27b0', '#ef6c00', '#00897b', '#c62828', '#5d4037']

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  default: { prompt: 0.002, completion: 0.004 },
  'gpt-4o-mini': { prompt: 0.00015, completion: 0.0006 },
  'gpt-4o': { prompt: 0.0025, completion: 0.005 },
}

function calculateCost(model: string | undefined, prompt: number, completion: number) {
  const pricing = MODEL_PRICING[model ?? ''] ?? MODEL_PRICING.default
  return (prompt / 1000) * pricing.prompt + (completion / 1000) * pricing.completion
}

export default function TokenVisualization({ events }: { events: SessionEvent[] }) {
  const tokenData = useMemo(() => {
    const tokenEvents: TokenEvent[] = events
      .filter((event) => event.event_type === 'llm_response_received' && event.metadata)
      .map((event) => ({
        role: (event.metadata?.agent_role as string) || 'unknown',
        model: event.metadata?.model as string | undefined,
        promptTokens: Number(event.metadata?.prompt_tokens ?? 0),
        completionTokens: Number(event.metadata?.completion_tokens ?? 0),
        totalTokens: Number(event.metadata?.total_tokens ?? 0),
        timestamp: new Date(event.timestamp),
      }))
      .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())

    const totals = new Map<string, number>()
    let cumulativeTotal = 0
    const cumulativePoints: { timestamp: Date; cumulative: number }[] = []
    let estimatedCost = 0

    tokenEvents.forEach((entry) => {
      totals.set(entry.role, (totals.get(entry.role) ?? 0) + entry.totalTokens)
      cumulativeTotal += entry.totalTokens
      estimatedCost += calculateCost(entry.model, entry.promptTokens, entry.completionTokens)
      cumulativePoints.push({ timestamp: entry.timestamp, cumulative: cumulativeTotal })
    })

    return {
      tokenEvents,
      totals,
      cumulativePoints,
      cumulativeTotal,
      estimatedCost,
    }
  }, [events])

  const { tokenEvents, totals, cumulativePoints, cumulativeTotal, estimatedCost } = tokenData
  const budgetLimit = 5 // dollars
  const budgetUsage = estimatedCost / budgetLimit

  const pieGradient = useMemo(() => {
    if (cumulativeTotal === 0) return '#e0e0e0'

    let start = 0
    const slices: string[] = []
    Array.from(totals.entries()).forEach(([role, total], idx) => {
      const portion = (total / cumulativeTotal) * 100
      const end = start + portion
      const color = ROLE_COLORS[idx % ROLE_COLORS.length]
      slices.push(`${color} ${start}% ${end}%`)
      start = end
    })

    return `conic-gradient(${slices.join(', ')})`
  }, [totals, cumulativeTotal])

  const linePoints = useMemo(() => {
    if (cumulativePoints.length === 0) return ''
    const maxTokens = Math.max(...cumulativePoints.map((pt) => pt.cumulative), 1)

    return cumulativePoints
      .map((pt, idx) => {
        const x = (idx / Math.max(cumulativePoints.length - 1, 1)) * 100
        const y = 100 - (pt.cumulative / maxTokens) * 100
        return `${x},${y}`
      })
      .join(' ')
  }, [cumulativePoints])

  return (
    <section>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px',
        }}
      >
        <h2 style={{ margin: 0 }}>Token Usage</h2>
        <span style={{ fontSize: '12px', opacity: 0.7 }}>
          Real-time token and cost estimates
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '12px',
        }}
      >
        <div
          style={{
            background: '#f8f9fa',
            border: '1px solid #e0e0e0',
            borderRadius: '10px',
            padding: '12px',
          }}
        >
          <div style={{ fontSize: '12px', opacity: 0.7, marginBottom: '4px' }}>Totals</div>
          <div style={{ fontWeight: 700, fontSize: '22px' }}>{cumulativeTotal} tokens</div>
          <div style={{ fontSize: '13px', opacity: 0.7 }}>
            Est. cost ${estimatedCost.toFixed(4)} / ${budgetLimit.toFixed(0)} budget
          </div>
          <div
            style={{
              marginTop: '12px',
              height: '10px',
              borderRadius: '999px',
              overflow: 'hidden',
              background: '#e0e0e0',
            }}
          >
            <div
              style={{
                width: `${Math.min(budgetUsage * 100, 100)}%`,
                height: '100%',
                background: budgetUsage > 1 ? '#d32f2f' : budgetUsage > 0.75 ? '#f9a825' : '#2e7d32',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>

        <div
          style={{
            background: '#f8f9fa',
            border: '1px solid #e0e0e0',
            borderRadius: '10px',
            padding: '12px',
            display: 'flex',
            gap: '12px',
            alignItems: 'center',
            minHeight: '160px',
          }}
        >
          <div
            style={{
              width: '140px',
              height: '140px',
              borderRadius: '50%',
              background: pieGradient,
              border: '1px solid #ddd',
              flexShrink: 0,
            }}
          />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, marginBottom: '8px' }}>Tokens by agent</div>
            {Array.from(totals.entries()).length === 0 ? (
              <p style={{ opacity: 0.6 }}>Waiting for LLM responses...</p>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '6px' }}>
                {Array.from(totals.entries()).map(([role, total], idx) => (
                  <li
                    key={role}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          width: '10px',
                          height: '10px',
                          borderRadius: '50%',
                          background: ROLE_COLORS[idx % ROLE_COLORS.length],
                        }}
                      />
                      <span style={{ textTransform: 'capitalize' }}>{role}</span>
                    </div>
                    <span style={{ fontWeight: 700 }}>{total} tokens</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div
          style={{
            background: '#f8f9fa',
            border: '1px solid #e0e0e0',
            borderRadius: '10px',
            padding: '12px',
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: '8px' }}>Cumulative burn</div>
          {cumulativePoints.length === 0 ? (
            <p style={{ opacity: 0.6 }}>Tokens will appear as the run progresses.</p>
          ) : (
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height: '160px' }}>
              <rect x="0" y="0" width="100" height="100" fill="#fff" stroke="#e0e0e0" />
              <polyline
                points={linePoints}
                fill="none"
                stroke="#1976d2"
                strokeWidth="2"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            </svg>
          )}
        </div>
      </div>

      {tokenEvents.length > 0 && (
        <div style={{ marginTop: '12px', fontSize: '12px', opacity: 0.7 }}>
          Latest update: {tokenEvents[tokenEvents.length - 1].timestamp.toLocaleTimeString()}
        </div>
      )}
    </section>
  )
}
