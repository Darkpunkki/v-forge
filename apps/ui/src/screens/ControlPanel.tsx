import { useEffect, useState } from "react";
import {
  getControlContext,
  streamSessionEvents,
  type SessionEvent,
} from "../api/controlClient";
import AgentDashboard from "./control/widgets/AgentDashboard";
import ExecutionTimeline from "./control/widgets/ExecutionTimeline";
import EventStream from "./control/widgets/EventStream";
import GateLog from "./control/widgets/GateLog";
import ModelRouter from "./control/widgets/ModelRouter";
import PromptInspector from "./control/widgets/PromptInspector";
import TokenVisualization from "./control/widgets/TokenVisualization";
import CostAnalytics from "./control/widgets/CostAnalytics";

export function ControlPanelScreen() {
  const [controlSessionId, setControlSessionId] = useState<string | null>(null);
  const [sessionEvents, setSessionEvents] = useState<SessionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sseError, setSseError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadContext() {
      setLoading(true);
      setError(null);
      try {
        const context = await getControlContext();
        if (!cancelled) {
          setControlSessionId(context.control_session_id);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err?.detail || err?.message || String(err));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadContext();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!controlSessionId) {
      setSessionEvents([]);
      setSseError(null);
      return;
    }

    setSessionEvents([]);
    setSseError(null);

    const sessionId = controlSessionId;
    let cancelled = false;

    const eventSource = streamSessionEvents(sessionId);

    const handleEvent = (e: MessageEvent) => {
      if (cancelled) return;
      try {
        const event: SessionEvent = JSON.parse(e.data);
        setSessionEvents((prev) => {
          const next = [...prev, event];
          return next.length > 500 ? next.slice(next.length - 500) : next;
        });
      } catch (parseErr) {
        console.error("Failed to parse SSE event:", parseErr, e.data);
      }
    };

    eventSource.addEventListener("session_event", handleEvent);

    eventSource.onerror = (err) => {
      console.error("SSE error:", err);
      if (!cancelled) {
        setSseError("Real-time updates disconnected");
      }
      eventSource.close();
    };

    return () => {
      cancelled = true;
      eventSource.removeEventListener("session_event", handleEvent);
      eventSource.close();
    };
  }, [controlSessionId]);

  if (loading) {
    return (
      <div style={{ padding: "24px" }}>
        <h1>Control Panel</h1>
        <p>Loading sessions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "24px" }}>
        <h1>Control Panel</h1>
        <pre style={{ background: "#fee", padding: 12 }}>{error}</pre>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px" }}>
      <header style={{ marginBottom: "24px" }}>
        <h1 style={{ marginTop: 0 }}>Control Panel</h1>
        <p style={{ opacity: 0.7 }}>
          Real-time control observability and agent monitoring
        </p>
      </header>

      <section
        style={{
          marginBottom: "16px",
          display: "flex",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div
          style={{
            background: "#f5f5f5",
            padding: "12px 16px",
            borderRadius: "8px",
            border: "1px solid #e0e0e0",
          }}
        >
          <div
            style={{
              fontSize: "12px",
              opacity: 0.7,
              textTransform: "uppercase",
            }}
          >
            Control Context
          </div>
          <div style={{ fontWeight: 600 }}>
            {controlSessionId ?? "Unavailable"}
          </div>
        </div>
      </section>

      {sseError && (
        <div
          style={{
            background: "#fff3cd",
            border: "1px solid #ffc107",
            color: "#856404",
            padding: "12px 16px",
            borderRadius: "4px",
            marginBottom: "16px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>!</span>
          <span>{sseError}</span>
        </div>
      )}

      <section>
        <h2>Monitoring</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
            gap: "16px",
          }}
        >
          <AgentDashboard events={sessionEvents} />
          <TokenVisualization events={sessionEvents} />
          <ExecutionTimeline events={sessionEvents} />
          <GateLog events={sessionEvents} />
          <ModelRouter events={sessionEvents} />
          {controlSessionId && (
            <EventStream
              events={sessionEvents}
              sessionId={controlSessionId}
              onClear={() => setSessionEvents([])}
            />
          )}
          {controlSessionId && <PromptInspector sessionId={controlSessionId} />}
          <CostAnalytics events={sessionEvents} />
        </div>
      </section>
    </div>
  );
}
