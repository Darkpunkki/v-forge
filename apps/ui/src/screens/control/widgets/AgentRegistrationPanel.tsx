import React, { useMemo, useState } from 'react'
import { registerAgent, type RemoteAgent } from '../../../api/controlClient'

type AgentRegistrationPanelProps = {
  onRegistered: (agent: RemoteAgent) => void
  defaultEndpointUrl?: string
}

const DEFAULT_ENDPOINT_URL = 'ws://localhost:8000/ws/agent-bridge'

function isValidEndpoint(value: string): boolean {
  try {
    const url = new URL(value)
    return ['ws:', 'wss:', 'http:', 'https:'].includes(url.protocol)
  } catch {
    return false
  }
}

export function AgentRegistrationPanel({
  onRegistered,
  defaultEndpointUrl = '',
}: AgentRegistrationPanelProps) {
  const [name, setName] = useState('')
  const [endpointUrl, setEndpointUrl] = useState(defaultEndpointUrl)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{ name?: string; endpointUrl?: string }>({})

  const placeholderUrl = useMemo(() => {
    return defaultEndpointUrl || DEFAULT_ENDPOINT_URL
  }, [defaultEndpointUrl])

  const validate = () => {
    const errors: { name?: string; endpointUrl?: string } = {}
    if (!name.trim()) {
      errors.name = 'Name is required'
    }
    if (!endpointUrl.trim()) {
      errors.endpointUrl = 'Endpoint URL is required'
    } else if (!isValidEndpoint(endpointUrl.trim())) {
      errors.endpointUrl = 'Endpoint URL must be a valid ws://, wss://, http://, or https:// URL'
    }
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (!validate()) return

    setSaving(true)
    try {
      const response = await registerAgent(name.trim(), endpointUrl.trim())
      setSuccess(`Registered ${response.agent.name}`)
      setName('')
      setEndpointUrl(defaultEndpointUrl)
      onRegistered(response.agent)
    } catch (err: any) {
      setError(err?.detail || err?.message || 'Failed to register agent')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section
      style={{
        background: '#f5f5f5',
        border: '1px solid #e0e0e0',
        borderRadius: '10px',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      <div>
        <h3 style={{ margin: 0, marginBottom: '4px' }}>Register Agent</h3>
        <p style={{ margin: 0, fontSize: '12px', opacity: 0.7 }}>
          Add a remote agent connection to the control plane.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '10px' }}>
        <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
          Agent name
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Agent Alpha"
            style={{
              padding: '8px 10px',
              borderRadius: '6px',
              border: `1px solid ${fieldErrors.name ? '#c62828' : '#ccc'}`,
            }}
          />
          {fieldErrors.name && (
            <span style={{ color: '#c62828', fontSize: '12px' }}>{fieldErrors.name}</span>
          )}
        </label>

        <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
          Endpoint URL
          <input
            type="text"
            value={endpointUrl}
            onChange={(event) => setEndpointUrl(event.target.value)}
            placeholder={placeholderUrl}
            style={{
              padding: '8px 10px',
              borderRadius: '6px',
              border: `1px solid ${fieldErrors.endpointUrl ? '#c62828' : '#ccc'}`,
            }}
          />
          {fieldErrors.endpointUrl && (
            <span style={{ color: '#c62828', fontSize: '12px' }}>
              {fieldErrors.endpointUrl}
            </span>
          )}
        </label>

        <button
          type="submit"
          disabled={saving}
          style={{
            padding: '10px 12px',
            borderRadius: '6px',
            border: '1px solid #111',
            background: saving ? '#ddd' : '#111',
            color: saving ? '#555' : '#fff',
            fontWeight: 600,
            cursor: saving ? 'not-allowed' : 'pointer',
          }}
        >
          {saving ? 'Registering...' : 'Register Agent'}
        </button>
      </form>

      {error && (
        <div
          style={{
            background: '#ffebee',
            border: '1px solid #ef9a9a',
            color: '#b71c1c',
            borderRadius: '6px',
            padding: '8px 10px',
            fontSize: '12px',
          }}
        >
          {error}
        </div>
      )}

      {success && (
        <div
          style={{
            background: '#e8f5e9',
            border: '1px solid #a5d6a7',
            color: '#2e7d32',
            borderRadius: '6px',
            padding: '8px 10px',
            fontSize: '12px',
          }}
        >
          {success}
        </div>
      )}
    </section>
  )
}

export default AgentRegistrationPanel
