import { useMemo } from 'react'

import type { SessionEvent } from '../../../api/controlClient'
import './CostAnalytics.css'

type CostAnalyticsProps = {
  events: SessionEvent[]
  budgetUSD?: number
}

type ModelCost = {
  model: string
  promptTokens: number
  completionTokens: number
  totalTokens: number
  cost: number
}

type BurnPoint = {
  timestamp: Date
  cumulativeCost: number
}

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  'gpt-4o': { prompt: 2.5, completion: 10.0 },
  'gpt-4o-mini': { prompt: 0.15, completion: 0.6 },
  'claude-sonnet-4': { prompt: 3.0, completion: 15.0 },
  'claude-opus-4': { prompt: 15.0, completion: 75.0 },
  default: { prompt: 1.0, completion: 2.0 },
}

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

function calculateCost(model: string, promptTokens: number, completionTokens: number) {
  const pricing = MODEL_PRICING[model] ?? MODEL_PRICING.default
  return (promptTokens / 1_000_000) * pricing.prompt + (completionTokens / 1_000_000) * pricing.completion
}

export default function CostAnalytics({ events, budgetUSD = 2 }: CostAnalyticsProps) {
  const { costsByModel, totalCost, burnRate } = useMemo(() => {
    const costs = new Map<string, ModelCost>()
    const burn: BurnPoint[] = []
    let cumulativeCost = 0

    const tokenEvents = events
      .filter((event) => event.event_type === 'llm_response_received' && event.metadata)
      .map((event) => ({
        model: String(event.metadata?.model ?? 'unknown'),
        promptTokens: Number(event.metadata?.prompt_tokens ?? 0),
        completionTokens: Number(event.metadata?.completion_tokens ?? 0),
        timestamp: new Date(event.timestamp),
      }))
      .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())

    tokenEvents.forEach((event) => {
      const cost = calculateCost(event.model, event.promptTokens, event.completionTokens)
      const existing = costs.get(event.model)
      const totalTokens = event.promptTokens + event.completionTokens

      if (existing) {
        existing.promptTokens += event.promptTokens
        existing.completionTokens += event.completionTokens
        existing.totalTokens += totalTokens
        existing.cost += cost
      } else {
        costs.set(event.model, {
          model: event.model,
          promptTokens: event.promptTokens,
          completionTokens: event.completionTokens,
          totalTokens,
          cost,
        })
      }

      cumulativeCost += cost
      burn.push({ timestamp: event.timestamp, cumulativeCost })
    })

    return {
      costsByModel: Array.from(costs.values()).sort((a, b) => b.cost - a.cost),
      totalCost: cumulativeCost,
      burnRate: burn,
    }
  }, [events])

  const budgetUsedPercent = budgetUSD > 0 ? (totalCost / budgetUSD) * 100 : 0
  const budgetRemaining = budgetUSD - totalCost

  const pieGradient = useMemo(() => {
    if (costsByModel.length === 0 || totalCost === 0) return '#e2e8f0'

    let start = 0
    const slices: string[] = []
    costsByModel.forEach((entry, index) => {
      const portion = (entry.cost / totalCost) * 100
      const end = start + portion
      slices.push(`${COLORS[index % COLORS.length]} ${start}% ${end}%`)
      start = end
    })

    return `conic-gradient(${slices.join(', ')})`
  }, [costsByModel, totalCost])

  const maxTokens = Math.max(...costsByModel.map((entry) => entry.totalTokens), 1)

  const burnPoints = useMemo(() => {
    if (burnRate.length === 0) return ''
    const maxCost = Math.max(...burnRate.map((entry) => entry.cumulativeCost), 1)

    return burnRate
      .map((entry, idx) => {
        const x = (idx / Math.max(burnRate.length - 1, 1)) * 100
        const y = 100 - (entry.cumulativeCost / maxCost) * 100
        return `${x},${y}`
      })
      .join(' ')
  }, [burnRate])

  return (
    <section className="cost-analytics">
      <header className="cost-analytics__header">
        <div>
          <h2>Cost Analytics</h2>
          <p>Token spend by model, burn rate, and budget alerts.</p>
        </div>
        <div className="cost-analytics__summary">
          <span>Total spend</span>
          <strong>${totalCost.toFixed(4)}</strong>
        </div>
      </header>

      <div className={`cost-analytics__budget ${budgetUsedPercent >= 100 ? 'critical' : budgetUsedPercent >= 80 ? 'warning' : ''}`}>
        <div className="cost-analytics__budget-header">
          <span>Budget</span>
          <strong>${totalCost.toFixed(4)} / ${budgetUSD.toFixed(2)}</strong>
        </div>
        <div className="cost-analytics__budget-bar">
          <div
            className="cost-analytics__budget-fill"
            style={{ width: `${Math.min(budgetUsedPercent, 100)}%` }}
          />
        </div>
        <div className="cost-analytics__budget-footer">
          {budgetRemaining >= 0
            ? `${budgetRemaining.toFixed(4)} remaining (${Math.max(100 - budgetUsedPercent, 0).toFixed(1)}%)`
            : `Budget exceeded by ${Math.abs(budgetRemaining).toFixed(4)}`}
        </div>
      </div>

      <div className="cost-analytics__grid">
        <div className="cost-analytics__card">
          <h3>Cost distribution</h3>
          <div className="cost-analytics__pie" style={{ background: pieGradient }} />
          {costsByModel.length === 0 ? (
            <p className="cost-analytics__empty">No cost data yet.</p>
          ) : (
            <ul className="cost-analytics__legend">
              {costsByModel.map((entry, index) => (
                <li key={entry.model}>
                  <span
                    className="cost-analytics__swatch"
                    style={{ background: COLORS[index % COLORS.length] }}
                  />
                  <span>{entry.model}</span>
                  <strong>${entry.cost.toFixed(4)}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="cost-analytics__card">
          <h3>Token mix by model</h3>
          {costsByModel.length === 0 ? (
            <p className="cost-analytics__empty">Waiting for LLM responses.</p>
          ) : (
            <div className="cost-analytics__bars">
              {costsByModel.map((entry) => (
                <div key={entry.model} className="cost-analytics__bar-row">
                  <div className="cost-analytics__bar-label">
                    <span>{entry.model}</span>
                    <strong>{entry.totalTokens.toLocaleString()} tokens</strong>
                  </div>
                  <div className="cost-analytics__bar">
                    <div
                      className="cost-analytics__bar-fill prompt"
                      style={{ width: `${(entry.promptTokens / maxTokens) * 100}%` }}
                    />
                    <div
                      className="cost-analytics__bar-fill completion"
                      style={{ width: `${(entry.completionTokens / maxTokens) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="cost-analytics__card">
          <h3>Burn rate</h3>
          {burnRate.length === 0 ? (
            <p className="cost-analytics__empty">Burn rate updates after responses arrive.</p>
          ) : (
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="cost-analytics__sparkline">
              <rect x="0" y="0" width="100" height="100" fill="#fff" stroke="#e2e8f0" />
              <polyline
                points={burnPoints}
                fill="none"
                stroke="#6366f1"
                strokeWidth="2"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            </svg>
          )}
          {burnRate.length > 0 && (
            <div className="cost-analytics__updated">
              Latest update: {burnRate[burnRate.length - 1].timestamp.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      <div className="cost-analytics__table">
        <h3>Detailed breakdown</h3>
        {costsByModel.length === 0 ? (
          <p className="cost-analytics__empty">No costs recorded yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Prompt tokens</th>
                <th>Completion tokens</th>
                <th>Total tokens</th>
                <th>Cost (USD)</th>
              </tr>
            </thead>
            <tbody>
              {costsByModel.map((entry) => (
                <tr key={entry.model}>
                  <td>{entry.model}</td>
                  <td>{entry.promptTokens.toLocaleString()}</td>
                  <td>{entry.completionTokens.toLocaleString()}</td>
                  <td>{entry.totalTokens.toLocaleString()}</td>
                  <td>${entry.cost.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td>Total</td>
                <td>{costsByModel.reduce((sum, entry) => sum + entry.promptTokens, 0).toLocaleString()}</td>
                <td>{costsByModel.reduce((sum, entry) => sum + entry.completionTokens, 0).toLocaleString()}</td>
                <td>{costsByModel.reduce((sum, entry) => sum + entry.totalTokens, 0).toLocaleString()}</td>
                <td>${totalCost.toFixed(4)}</td>
              </tr>
            </tfoot>
          </table>
        )}
      </div>
    </section>
  )
}
