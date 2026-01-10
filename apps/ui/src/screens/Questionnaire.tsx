import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getQuestion, submitAnswer, getProgress } from '../api/client'
import type { QuestionResponse } from '../types/api'

export function QuestionnaireScreen() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [question, setQuestion] = useState<QuestionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  // State for different input types
  const [selectedRadio, setSelectedRadio] = useState<string>('')
  const [selectedCheckboxes, setSelectedCheckboxes] = useState<Set<string>>(new Set())
  const [selectedDropdown, setSelectedDropdown] = useState<string>('')
  const [sliderValue, setSliderValue] = useState<number>(0)

  async function routeFromPhase() {
    if (!sessionId) return
    const p = await getProgress(sessionId)

    switch (p.phase) {
      case 'PLAN_REVIEW':
        navigate(`/plan/${sessionId}`, { replace: true })
        return
      case 'CLARIFICATION':
        navigate(`/clarification/${sessionId}`, { replace: true })
        return
      case 'COMPLETE':
      case 'FAILED':
        navigate(`/result/${sessionId}`, { replace: true })
        return
      default:
        // QUESTIONNAIRE / BUILD_SPEC / IDEA / EXECUTION / VERIFICATION etc.
        navigate(`/progress/${sessionId}`, { replace: true })
        return
    }
  }

  async function loadQuestion() {
    if (!sessionId) return

    setError(null)
    setLoading(true)

    // Reset form state
    setSelectedRadio('')
    setSelectedCheckboxes(new Set())
    setSelectedDropdown('')
    setSliderValue(0)

    try {
      const q = await getQuestion(sessionId)
      setQuestion(q)

      // Initialize slider value to middle of range if it's a slider question
      if (q.question_type === 'slider' && q.min_value !== undefined && q.max_value !== undefined) {
        setSliderValue(Math.floor((q.min_value + q.max_value) / 2))
      }
    } catch (err: any) {
      // If backend says "no question" (common when phase moved on), route by phase
      if (err?.status === 400) {
        try {
          await routeFromPhase()
          return
        } catch (e: any) {
          setError(e?.detail || e?.message || String(e))
          return
        }
      }
      setError(err?.detail || err?.message || String(err))
    }
    finally {
      setLoading(false)
    }
  }

  async function handleSubmit() {
    if (!sessionId || !question) return

    let answer: string

    // Determine answer based on question type
    switch (question.question_type) {
      case 'radio':
        if (!selectedRadio) {
          setError('Please select an option')
          return
        }
        answer = selectedRadio
        break

      case 'checkbox':
        if (selectedCheckboxes.size === 0) {
          setError('Please select at least one option')
          return
        }
        // Join multiple selections with commas
        answer = Array.from(selectedCheckboxes).join(',')
        break

      case 'select':
        if (!selectedDropdown) {
          setError('Please select an option')
          return
        }
        answer = selectedDropdown
        break

      case 'slider':
        answer = String(sliderValue)
        break

      default:
        setError(`Unknown question type: ${question.question_type}`)
        return
    }

    setError(null)
    setSubmitting(true)

    try {
      const response = await submitAnswer(sessionId, {
        question_id: question.question_id,
        answer,
      })

      if (response.is_complete) {
        // Questionnaire complete; session likely moved to PLAN_REVIEW or beyond
        await routeFromPhase()
      } else {
        await loadQuestion()
      }

    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setSubmitting(false)
    }
  }

  function handleCheckboxChange(value: string, checked: boolean) {
    setSelectedCheckboxes(prev => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(value)
      } else {
        newSet.delete(value)
      }
      return newSet
    })
  }

  useEffect(() => {
    loadQuestion()
  }, [sessionId])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <p>Loading question...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h2>Error</h2>
        <pre style={{ background: '#fee', padding: 12, borderRadius: 6 }}>{error}</pre>
        <button onClick={() => navigate('/')} style={{ marginTop: 16 }}>
          Back to Home
        </button>
      </div>
    )
  }

  if (!question) {
    return <div>No question available</div>
  }

  return (
    <div>
      {/* Question progress indicator */}
      {question.is_final && (
        <div style={{
          background: '#fff3cd',
          padding: 8,
          borderRadius: 6,
          marginBottom: 16,
          fontSize: '0.9em',
          textAlign: 'center'
        }}>
          <strong>Final Question</strong>
        </div>
      )}

      <div style={{
        border: '1px solid #ddd',
        borderRadius: 12,
        padding: 24,
        background: '#fff'
      }}>
        <h2 style={{ marginTop: 0, marginBottom: 8 }}>{question.text}</h2>

        {/* Question type indicator for debugging/clarity */}
        <p style={{
          fontSize: '0.85em',
          opacity: 0.6,
          marginTop: 0,
          marginBottom: 24
        }}>
          Type: {question.question_type}
        </p>

        {/* Radio buttons */}
        {question.question_type === 'radio' && question.options && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {question.options.map((opt) => (
              <label
                key={opt.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: 12,
                  border: '1px solid #ddd',
                  borderRadius: 6,
                  cursor: 'pointer',
                  background: selectedRadio === opt.value ? '#e3f2fd' : '#fff',
                }}
              >
                <input
                  type="radio"
                  name="question"
                  value={opt.value}
                  checked={selectedRadio === opt.value}
                  onChange={(e) => setSelectedRadio(e.target.value)}
                  style={{ marginRight: 12 }}
                />
                <span>{opt.label}</span>
              </label>
            ))}
          </div>
        )}

        {/* Checkboxes */}
        {question.question_type === 'checkbox' && question.options && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {question.options.map((opt) => (
              <label
                key={opt.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: 12,
                  border: '1px solid #ddd',
                  borderRadius: 6,
                  cursor: 'pointer',
                  background: selectedCheckboxes.has(opt.value) ? '#e8f5e9' : '#fff',
                }}
              >
                <input
                  type="checkbox"
                  value={opt.value}
                  checked={selectedCheckboxes.has(opt.value)}
                  onChange={(e) => handleCheckboxChange(opt.value, e.target.checked)}
                  style={{ marginRight: 12 }}
                />
                <span>{opt.label}</span>
              </label>
            ))}
          </div>
        )}

        {/* Select dropdown */}
        {question.question_type === 'select' && question.options && (
          <div>
            <select
              value={selectedDropdown}
              onChange={(e) => setSelectedDropdown(e.target.value)}
              style={{
                width: '100%',
                padding: 12,
                fontSize: '1em',
                border: '1px solid #ddd',
                borderRadius: 6,
                background: '#fff',
              }}
            >
              <option value="">-- Select an option --</option>
              {question.options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Slider */}
        {question.question_type === 'slider' &&
          question.min_value !== undefined &&
          question.max_value !== undefined && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <input
                  type="range"
                  min={question.min_value}
                  max={question.max_value}
                  value={sliderValue}
                  onChange={(e) => setSliderValue(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '0.9em',
                  marginTop: 8,
                  opacity: 0.7
                }}>
                  <span>{question.min_value}</span>
                  <strong style={{ fontSize: '1.2em', opacity: 1 }}>{sliderValue}</strong>
                  <span>{question.max_value}</span>
                </div>
              </div>
            </div>
          )}

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={submitting}
          style={{
            marginTop: 24,
            padding: '12px 24px',
            fontSize: '1em',
            background: '#0070f3',
            color: 'white',
            border: 'none',
            borderRadius: 6,
            cursor: submitting ? 'not-allowed' : 'pointer',
            opacity: submitting ? 0.6 : 1,
          }}
        >
          {submitting ? 'Submitting...' : 'Submit Answer'}
        </button>
      </div>
    </div>
  )
}
