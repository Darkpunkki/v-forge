import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getPlan, decidePlan } from "../api/client";
import type { PlanResponse } from "../types/api";

export function PlanReviewScreen() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadPlan() {
    if (!sessionId) return;

    setError(null);
    setLoading(true);

    try {
      const p = await getPlan(sessionId);
      setPlan(p);
    } catch (err: any) {
      setError(err?.detail || err?.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  const [submitting, setSubmitting] = useState(false);

  async function handleDecision(decision: "approve" | "reject") {
    if (!sessionId) return;

    setError(null);
    setSubmitting(true);

    try {
      const response = await decidePlan(sessionId, decision);

      switch (response.next_phase) {
        case "PLAN_REVIEW":
          // Still in review (e.g., rejected but staying in review, or needs edits)
          await loadPlan();
          return;

        case "CLARIFICATION":
          navigate(`/clarification/${sessionId}`, { replace: true });
          return;

        case "COMPLETE":
        case "FAILED":
          navigate(`/result/${sessionId}`, { replace: true });
          return;

        default:
          // EXECUTION / VERIFICATION / BUILD_SPEC / IDEA etc.
          navigate(`/progress/${sessionId}`, { replace: true });
          return;
      }
    } catch (err: any) {
      setError(err?.detail || err?.message || String(err));
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    loadPlan();
  }, [sessionId]);

  if (loading) {
    return <div>Loading plan...</div>;
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

  if (!plan) {
    return <div>No plan available</div>;
  }

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <h1>Plan Review</h1>
      <p style={{ color: "#666", marginBottom: 24 }}>
        Review the proposed plan and approve to begin implementation.
      </p>

      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 12,
          padding: 24,
          background: "#fafafa",
        }}
      >
        <section style={{ marginBottom: 24 }}>
          <h2 style={{ marginTop: 0, fontSize: 20, color: "#0070f3" }}>
            Features
          </h2>
          <ul style={{ lineHeight: 1.8 }}>
            {plan.features.map((feature, idx) => (
              <li key={idx}>{feature}</li>
            ))}
          </ul>
        </section>

        <section style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 20, color: "#0070f3" }}>Plan Details</h2>
          <div
            style={{
              background: "white",
              padding: 16,
              borderRadius: 8,
              marginTop: 12,
            }}
          >
            <p style={{ margin: "8px 0" }}>
              <strong>Task Count:</strong> {plan.task_count}
            </p>
            <p style={{ margin: "8px 0" }}>
              <strong>Estimated Scope:</strong> {plan.estimated_scope}
            </p>
          </div>
        </section>

        <section style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 20, color: "#0070f3" }}>Verification Steps</h2>
          <ul style={{ lineHeight: 1.8 }}>
            {plan.verification_steps.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ul>
        </section>

        <section style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 20, color: "#0070f3" }}>Constraints</h2>
          <ul style={{ lineHeight: 1.8 }}>
            {plan.constraints.map((constraint, idx) => (
              <li key={idx}>{constraint}</li>
            ))}
          </ul>
        </section>

        {error && (
          <div
            style={{
              background: "#fee",
              padding: 12,
              borderRadius: 6,
              marginBottom: 16,
              color: "#c00",
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        <div style={{ display: "flex", gap: 12, marginTop: 32 }}>
          <button
            onClick={() => handleDecision("approve")}
            disabled={submitting}
            style={{
              padding: "12px 32px",
              background: submitting ? "#ccc" : "#0070f3",
              color: "white",
              border: "none",
              borderRadius: 6,
              fontSize: 16,
              fontWeight: 600,
              cursor: submitting ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
          >
            {submitting ? "Submitting..." : "Approve Plan"}
          </button>
          <button
            onClick={() => handleDecision("reject")}
            disabled={submitting}
            style={{
              padding: "12px 32px",
              background: submitting ? "#ccc" : "#f44336",
              color: "white",
              border: "none",
              borderRadius: 6,
              fontSize: 16,
              fontWeight: 600,
              cursor: submitting ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
          >
            {submitting ? "Submitting..." : "Reject Plan"}
          </button>
        </div>
      </div>
    </div>
  );
}
