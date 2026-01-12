import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getClarification,
  submitClarification,
  getProgress,
} from "../api/client";
import type { ClarificationResponse } from "../types/api";

/**
 * Clarification screen for gates/agents that need user input
 */
export function ClarificationScreen() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [clarification, setClarification] =
    useState<ClarificationResponse | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  function formatError(err: unknown): string {
    if (!err) {
      return "Unknown error";
    }
    if (typeof err === "string") {
      return err;
    }
    if (err instanceof Error) {
      return err.message || String(err);
    }
    if (typeof err === "object") {
      const detail =
        (err as { detail?: unknown; message?: unknown }).detail ??
        (err as { message?: unknown }).message;
      if (detail) {
        return typeof detail === "string"
          ? detail
          : JSON.stringify(detail, null, 2);
      }
      return JSON.stringify(err, null, 2);
    }
    return String(err);
  }

  function formatContext(context: ClarificationResponse["context"]): string {
    if (!context) {
      return "";
    }
    if (typeof context === "string") {
      return context;
    }
    return JSON.stringify(context, null, 2);
  }

  async function routeFromPhase() {
    if (!sessionId) return;
    const p = await getProgress(sessionId);

    switch (p.phase) {
      case "CLARIFICATION":
        return; // stay here
      case "PLAN_REVIEW":
        navigate(`/plan/${sessionId}`, { replace: true });
        return;
      case "COMPLETE":
      case "FAILED":
        navigate(`/result/${sessionId}`, { replace: true });
        return;
      default:
        navigate(`/progress/${sessionId}`, { replace: true });
        return;
    }
  }

  async function loadClarification() {
    if (!sessionId) return;

    setError(null);
    setLoading(true);

    try {
      const c = await getClarification(sessionId);
      setSelectedAnswer(null);
      setClarification(c);
    } catch (err: any) {
      // If clarification isn't needed anymore (common: phase moved on), route by phase
      if (err?.status === 400) {
        try {
          await routeFromPhase();
          return;
        } catch (e: any) {
          setError(formatError(e));
          return;
        }
      }
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (!sessionId || !selectedAnswer) return;

    setError(null);
    setSubmitting(true);

    try {
      const res = await submitClarification(sessionId, {
        answer: selectedAnswer,
      });

      switch (res.next_phase) {
        case "PLAN_REVIEW":
          navigate(`/plan/${sessionId}`, { replace: true });
          return;
        case "CLARIFICATION":
          // Another clarification immediately needed; reload
          await loadClarification();
          return;
        case "COMPLETE":
        case "FAILED":
          navigate(`/result/${sessionId}`, { replace: true });
          return;
        default:
          navigate(`/progress/${sessionId}`, { replace: true });
          return;
      }
    } catch (err: any) {
      setError(formatError(err));
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    (async () => {
      await routeFromPhase();
      await loadClarification();
    })();
  }, [sessionId]);

  if (loading) {
    return <div>Loading clarification...</div>;
  }

  if (error) {
    return (
      <div>
        <h2>Error</h2>
        <pre style={{ background: "#fee", padding: 12 }}>{error}</pre>
        <button onClick={() => navigate("/")}>Back to Home</button>
      </div>
    );
  }

  if (!clarification) {
    return <div>No clarification available</div>;
  }

  return (
    <div style={{ maxWidth: 700, margin: "0 auto" }}>
      <div
        style={{
          background: "#fff3cd",
          padding: 20,
          borderRadius: 12,
          marginBottom: 24,
          border: "2px solid #ffc107",
        }}
      >
        <h1 style={{ margin: 0, fontSize: 24, color: "#856404" }}>
          ⚠️ Clarification Needed
        </h1>
        <p style={{ margin: "8px 0 0 0", color: "#856404" }}>
          Please answer the following question to continue
        </p>
      </div>

      <div
        style={{
          background: "white",
          border: "1px solid #ddd",
          borderRadius: 12,
          padding: 32,
        }}
      >
        {/* Question */}
        <h2 style={{ marginTop: 0, fontSize: 22, color: "#333" }}>
          {clarification.question}
        </h2>

        {/* Context (if provided) */}
        {formatContext(clarification.context) && (
          <div
            style={{
              background: "#f0f7ff",
              padding: 16,
              borderRadius: 8,
              marginBottom: 24,
              border: "1px solid #b3d9ff",
            }}
          >
            <p style={{ margin: 0, fontSize: 14, color: "#0056b3" }}>
              {formatContext(clarification.context)}
            </p>
          </div>
        )}

        {/* Options */}
        <div style={{ marginTop: 24 }}>
          {clarification.options.map((option) => {
            const isSelected = selectedAnswer === option.value;
            return (
              <div
                key={option.value}
                onClick={() => setSelectedAnswer(option.value)}
                style={{
                  border: isSelected ? "2px solid #0070f3" : "2px solid #ddd",
                  background: isSelected ? "#f0f7ff" : "white",
                  borderRadius: 8,
                  padding: 16,
                  marginBottom: 12,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
              >
                <div
                  style={{ display: "flex", alignItems: "flex-start", gap: 12 }}
                >
                  <div
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: "50%",
                      border: isSelected
                        ? "6px solid #0070f3"
                        : "2px solid #999",
                      flexShrink: 0,
                      marginTop: 2,
                      transition: "all 0.2s ease",
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: 16,
                        color: "#333",
                        marginBottom: 4,
                      }}
                    >
                      {option.label}
                    </div>
                    {option.description && (
                      <div
                        style={{ fontSize: 14, color: "#666", lineHeight: 1.5 }}
                      >
                        {option.description}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Error Display */}
        {error && (
          <div
            style={{
              background: "#fee",
              padding: 12,
              borderRadius: 6,
              marginTop: 16,
              color: "#c00",
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Submit Button */}
        <div style={{ marginTop: 32, display: "flex", gap: 12 }}>
          <button
            onClick={handleSubmit}
            disabled={!selectedAnswer || submitting}
            style={{
              flex: 1,
              padding: "14px 24px",
              background: !selectedAnswer || submitting ? "#ccc" : "#0070f3",
              color: "white",
              border: "none",
              borderRadius: 8,
              fontSize: 16,
              fontWeight: 600,
              cursor: !selectedAnswer || submitting ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
          >
            {submitting ? "Submitting..." : "Submit Answer"}
          </button>
        </div>
      </div>
    </div>
  );
}
