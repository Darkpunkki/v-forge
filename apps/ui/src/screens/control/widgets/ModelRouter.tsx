import { useMemo } from 'react'

import type { SessionEvent } from '../../../api/controlClient'
import './ModelRouter.css'

type RoutingDecision = {
  timestamp: string
  taskId: string
  agentRole: string
  modelTier: string
  reason: string
  failureCount: number
  model?: string
  estimatedCost: number
}

type ModelRouterProps = {
  events: SessionEvent[]
}

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  'gpt-4o': { prompt: 2.5, completion: 10.0 },
  'gpt-4o-mini': { prompt: 0.15, completion: 0.6 },
  'claude-sonnet-4': { prompt: 3.0, completion: 15.0 },
  'claude-opus-4': { prompt: 15.0, completion: 75.0 },
}

const TIER_FALLBACK: Record<string, { prompt: number; completion: number }> = {
  fast: { prompt: 0.2, completion: 0.8 },
  balanced: { prompt: 1.0, completion: 2.5 },
  powerful: { prompt: 3.0, completion: 12.0 },
}

function estimateCost(model: string | undefined, modelTier: string) {
  const pricing = model ? MODEL_PRICING[model] : undefined
  const fallback = TIER_FALLBACK[modelTier] || TIER_FALLBACK.balanced
  const { prompt, completion } = pricing || fallback
  return (1000 / 1_000_000) * prompt + (500 / 1_000_000) * completion
}

export default function ModelRouter({ events }: ModelRouterProps) {
  const decisions = useMemo(() => {
    const sorted = [...events].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

    const routedDecisions: RoutingDecision[] = []
    const latestByTaskRole = new Map<string, number>()

    sorted.forEach((event) => {
      if (event.event_type === 'model_routed') {
        const taskId = event.task_id || 'unknown'
        const agentRole = (event.metadata?.agent_role as string) || 'unknown'
        const modelTier = (event.metadata?.model_tier as string) || 'balanced'
        const failureCount = (event.metadata?.failure_count as number) || 0
        const reason =
          (event.metadata?.routing_reason as string) ||
          'Routing decision based on role and escalation policy.'

        const decision: RoutingDecision = {
          timestamp: event.timestamp,
          taskId,
          agentRole,
          modelTier,
          reason,
          failureCount,
          estimatedCost: estimateCost(undefined, modelTier),
        }

        routedDecisions.push(decision)
        latestByTaskRole.set(`${taskId}:${agentRole}`, routedDecisions.length - 1)
      }

      if (event.event_type === 'llm_response_received') {
        const taskId = event.task_id || 'unknown'
        const agentRole = (event.metadata?.agent_role as string) || 'unknown'
        const model = event.metadata?.model as string | undefined
        const index = latestByTaskRole.get(`${taskId}:${agentRole}`)

        if (index !== undefined && model) {
          const decision = routedDecisions[index]
          decision.model = model
          decision.estimatedCost = estimateCost(model, decision.modelTier)
        }
      }
    })

    return routedDecisions
      .sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )
  }, [events])

  const totals = useMemo(() => {
    return decisions.reduce(
      (acc, decision) => {
        acc.total += 1
        acc.escalations += decision.failureCount > 0 ? 1 : 0
        acc.cost += decision.estimatedCost
        return acc
      },
      { total: 0, escalations: 0, cost: 0 }
    )
  }, [decisions])

  return (
    <section className="model-router">
      <header className="model-router__header">
        <div>
          <h2>Model Routing Decisions</h2>
          <p>See why specific roles and model tiers were chosen for each task.</p>
        </div>
        <div className="model-router__stats">
          <div>
            <span>Total</span>
            <strong>{totals.total}</strong>
          </div>
          <div>
            <span>Escalations</span>
            <strong>{totals.escalations}</strong>
          </div>
          <div>
            <span>Est. Cost</span>
            <strong>${totals.cost.toFixed(4)}</strong>
          </div>
        </div>
      </header>

      <div className="model-router__body">
        {decisions.length === 0 ? (
          <div className="model-router__empty">No routing decisions yet.</div>
        ) : (
          <ul className="model-router__list">
            {decisions.map((decision, index) => (
              <li key={`${decision.taskId}-${decision.timestamp}-${index}`}>
                <div className="model-router__item">
                  <div className="model-router__item-header">
                    <span className={`model-router__badge model-router__badge--${decision.modelTier}`}>
                      {decision.model || decision.modelTier}
                    </span>
                    <span className="model-router__role">{decision.agentRole}</span>
                    {decision.failureCount > 0 && (
                      <span className="model-router__escalation">
                        Escalation (attempt {decision.failureCount + 1})
                      </span>
                    )}
                    <span className="model-router__time">
                      {new Date(decision.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="model-router__item-body">
                    <div className="model-router__task">Task: {decision.taskId}</div>
                    <div className="model-router__reason">{decision.reason}</div>
                    <div className="model-router__cost">
                      Estimated cost: ${decision.estimatedCost.toFixed(4)}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
