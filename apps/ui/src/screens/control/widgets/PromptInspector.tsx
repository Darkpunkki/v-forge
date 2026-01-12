import { useEffect, useMemo, useState } from 'react'
import { getSessionLlmTrace, type SessionLlmTrace } from '../../../api/controlClient'
import './PromptInspector.css'

type PromptInspectorProps = {
  sessionId: string
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function highlightPrompt(value: string) {
  const escaped = escapeHtml(value)
  return escaped
    .replace(/(\".*?\")/g, '<span class=\"prompt-inspector__token-string\">$1</span>')
    .replace(/\b(true|false|null)\b/g, '<span class=\"prompt-inspector__token-boolean\">$1</span>')
    .replace(/\b(\d+)\b/g, '<span class=\"prompt-inspector__token-number\">$1</span>')
}

export default function PromptInspector({ sessionId }: PromptInspectorProps) {
  const [traces, setTraces] = useState<SessionLlmTrace[]>([])
  const [selectedTrace, setSelectedTrace] = useState<SessionLlmTrace | null>(null)
  const [agentFilter, setAgentFilter] = useState('ALL')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadTraces() {
      setLoading(true)
      setError(null)
      try {
        const data = await getSessionLlmTrace(sessionId)
        if (cancelled) return
        setTraces(data.traces)
        setSelectedTrace(data.traces[0] ?? null)
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message || 'Unable to load LLM traces')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadTraces()
    return () => {
      cancelled = true
    }
  }, [sessionId])

  const agentOptions = useMemo(() => {
    const options = Array.from(
      new Set(traces.map((trace) => trace.agent_role).filter(Boolean))
    ) as string[]
    return ['ALL', ...options]
  }, [traces])

  const filteredTraces = useMemo(() => {
    if (agentFilter === 'ALL') return traces
    return traces.filter((trace) => trace.agent_role === agentFilter)
  }, [agentFilter, traces])

  const handleCopy = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setError(`${label} copied to clipboard.`)
      setTimeout(() => setError(null), 2000)
    } catch (err: any) {
      setError(err.message || 'Unable to copy prompt')
    }
  }

  return (
    <section className="prompt-inspector">
      <header className="prompt-inspector__header">
        <div>
          <h2>Prompt + Response Inspector</h2>
          <p>Review the exact prompts and responses captured for this session.</p>
        </div>
        <div className="prompt-inspector__controls">
          <select value={agentFilter} onChange={(event) => setAgentFilter(event.target.value)}>
            {agentOptions.map((agent) => (
              <option key={agent} value={agent}>
                {agent === 'ALL' ? 'All agents' : agent}
              </option>
            ))}
          </select>
        </div>
      </header>

      {error && <div className="prompt-inspector__alert">{error}</div>}

      <div className="prompt-inspector__layout">
        <aside className="prompt-inspector__list">
          {loading ? (
            <div className="prompt-inspector__empty">Loading traces...</div>
          ) : filteredTraces.length === 0 ? (
            <div className="prompt-inspector__empty">No prompts captured yet.</div>
          ) : (
            <ul>
              {filteredTraces.map((trace) => (
                <li
                  key={`${trace.timestamp}-${trace.task_id ?? trace.request_id}`}
                  className={
                    selectedTrace?.request_id === trace.request_id
                      ? 'prompt-inspector__item active'
                      : 'prompt-inspector__item'
                  }
                  onClick={() => setSelectedTrace(trace)}
                >
                  <div className="prompt-inspector__item-agent">{trace.agent_role ?? 'unknown'}</div>
                  <div className="prompt-inspector__item-model">{trace.model ?? 'unknown model'}</div>
                  <div className="prompt-inspector__item-task">
                    Task: {trace.task_id ?? '—'}
                  </div>
                  <div className="prompt-inspector__item-time">
                    {new Date(trace.timestamp).toLocaleTimeString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="prompt-inspector__viewer">
          {!selectedTrace ? (
            <div className="prompt-inspector__empty">Select a prompt to inspect.</div>
          ) : (
            <div className="prompt-inspector__details">
              <div className="prompt-inspector__meta">
                <div>
                  <span>Agent</span>
                  <strong>{selectedTrace.agent_role ?? 'unknown'}</strong>
                </div>
                <div>
                  <span>Model</span>
                  <strong>{selectedTrace.model ?? 'unknown'}</strong>
                </div>
                <div>
                  <span>Task</span>
                  <strong>{selectedTrace.task_id ?? '—'}</strong>
                </div>
                <div>
                  <span>Max tokens</span>
                  <strong>{selectedTrace.max_tokens ?? '—'}</strong>
                </div>
                <div>
                  <span>Temperature</span>
                  <strong>{selectedTrace.temperature ?? '—'}</strong>
                </div>
                <div>
                  <span>Response model</span>
                  <strong>{selectedTrace.response_model ?? '—'}</strong>
                </div>
                <div>
                  <span>Total tokens</span>
                  <strong>{selectedTrace.total_tokens ?? '—'}</strong>
                </div>
              </div>

              {selectedTrace.system_message && (
                <div className="prompt-inspector__section">
                  <div className="prompt-inspector__section-header">
                    <h3>System message</h3>
                    <button
                      type="button"
                      onClick={() => handleCopy(selectedTrace.system_message, 'System message')}
                    >
                      Copy
                    </button>
                  </div>
                  <pre
                    className="prompt-inspector__code"
                    dangerouslySetInnerHTML={{
                      __html: highlightPrompt(selectedTrace.system_message),
                    }}
                  />
                </div>
              )}

              <div className="prompt-inspector__section">
                <div className="prompt-inspector__section-header">
                  <h3>User prompt</h3>
                  <button
                    type="button"
                    onClick={() => handleCopy(selectedTrace.prompt, 'Prompt')}
                  >
                    Copy
                  </button>
                </div>
                <pre
                  className="prompt-inspector__code"
                  dangerouslySetInnerHTML={{
                    __html: highlightPrompt(
                      selectedTrace.prompt || 'No prompt text captured.'
                    ),
                  }}
                />
              </div>

              <div className="prompt-inspector__section">
                <div className="prompt-inspector__section-header">
                  <h3>LLM response</h3>
                  <button
                    type="button"
                    onClick={() => handleCopy(selectedTrace.response || '', 'Response')}
                    disabled={!selectedTrace.response}
                  >
                    Copy
                  </button>
                </div>
                <pre
                  className="prompt-inspector__code"
                  dangerouslySetInnerHTML={{
                    __html: highlightPrompt(
                      selectedTrace.response || 'No response captured yet.'
                    ),
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
