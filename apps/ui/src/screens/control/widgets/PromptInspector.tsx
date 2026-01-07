import { useEffect, useMemo, useState } from 'react'
import { getSessionPrompts, type SessionPrompt } from '../../../api/controlClient'
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
  const [prompts, setPrompts] = useState<SessionPrompt[]>([])
  const [selectedPrompt, setSelectedPrompt] = useState<SessionPrompt | null>(null)
  const [agentFilter, setAgentFilter] = useState('ALL')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadPrompts() {
      setLoading(true)
      setError(null)
      try {
        const data = await getSessionPrompts(sessionId)
        if (cancelled) return
        setPrompts(data.prompts)
        setSelectedPrompt(data.prompts[0] ?? null)
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message || 'Unable to load prompts')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadPrompts()
    return () => {
      cancelled = true
    }
  }, [sessionId])

  const agentOptions = useMemo(() => {
    const options = Array.from(
      new Set(prompts.map((prompt) => prompt.agent_role).filter(Boolean))
    ) as string[]
    return ['ALL', ...options]
  }, [prompts])

  const filteredPrompts = useMemo(() => {
    if (agentFilter === 'ALL') return prompts
    return prompts.filter((prompt) => prompt.agent_role === agentFilter)
  }, [agentFilter, prompts])

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
          <h2>Prompt Inspector</h2>
          <p>Review the exact prompts sent to agents in this session.</p>
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
            <div className="prompt-inspector__empty">Loading prompts...</div>
          ) : filteredPrompts.length === 0 ? (
            <div className="prompt-inspector__empty">No prompts captured yet.</div>
          ) : (
            <ul>
              {filteredPrompts.map((prompt) => (
                <li
                  key={`${prompt.timestamp}-${prompt.task_id ?? 'task'}`}
                  className={
                    selectedPrompt?.timestamp === prompt.timestamp
                      ? 'prompt-inspector__item active'
                      : 'prompt-inspector__item'
                  }
                  onClick={() => setSelectedPrompt(prompt)}
                >
                  <div className="prompt-inspector__item-agent">{prompt.agent_role ?? 'unknown'}</div>
                  <div className="prompt-inspector__item-model">{prompt.model ?? 'unknown model'}</div>
                  <div className="prompt-inspector__item-task">
                    Task: {prompt.task_id ?? '—'}
                  </div>
                  <div className="prompt-inspector__item-time">
                    {new Date(prompt.timestamp).toLocaleTimeString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="prompt-inspector__viewer">
          {!selectedPrompt ? (
            <div className="prompt-inspector__empty">Select a prompt to inspect.</div>
          ) : (
            <div className="prompt-inspector__details">
              <div className="prompt-inspector__meta">
                <div>
                  <span>Agent</span>
                  <strong>{selectedPrompt.agent_role ?? 'unknown'}</strong>
                </div>
                <div>
                  <span>Model</span>
                  <strong>{selectedPrompt.model ?? 'unknown'}</strong>
                </div>
                <div>
                  <span>Task</span>
                  <strong>{selectedPrompt.task_id ?? '—'}</strong>
                </div>
                <div>
                  <span>Max tokens</span>
                  <strong>{selectedPrompt.max_tokens ?? '—'}</strong>
                </div>
                <div>
                  <span>Temperature</span>
                  <strong>{selectedPrompt.temperature ?? '—'}</strong>
                </div>
              </div>

              {selectedPrompt.system_message && (
                <div className="prompt-inspector__section">
                  <div className="prompt-inspector__section-header">
                    <h3>System message</h3>
                    <button
                      type="button"
                      onClick={() => handleCopy(selectedPrompt.system_message, 'System message')}
                    >
                      Copy
                    </button>
                  </div>
                  <pre
                    className="prompt-inspector__code"
                    dangerouslySetInnerHTML={{
                      __html: highlightPrompt(selectedPrompt.system_message),
                    }}
                  />
                </div>
              )}

              <div className="prompt-inspector__section">
                <div className="prompt-inspector__section-header">
                  <h3>User prompt</h3>
                  <button
                    type="button"
                    onClick={() => handleCopy(selectedPrompt.prompt, 'Prompt')}
                  >
                    Copy
                  </button>
                </div>
                <pre
                  className="prompt-inspector__code"
                  dangerouslySetInnerHTML={{
                    __html: highlightPrompt(
                      selectedPrompt.prompt || 'No prompt text captured.'
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
