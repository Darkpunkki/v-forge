import { useEffect, useState } from "react";
import {
  getControlContext,
  streamSessionEvents,
  type RemoteAgent,
  type SessionEvent,
} from "../api/controlClient";
import AgentConnectionDashboard from "./control/widgets/AgentConnectionDashboard";
import AgentRegistrationPanel from "./control/widgets/AgentRegistrationPanel";
import CostAnalytics from "./control/widgets/CostAnalytics";
import EventStream from "./control/widgets/EventStream";
import StreamingOutputView from "./control/widgets/StreamingOutputView";
import TaskDispatchPanel from "./control/widgets/TaskDispatchPanel";
import "./ControlPanel.css";

export function ControlPanelScreen() {
  const [controlSessionId, setControlSessionId] = useState<string | null>(null);
  const [sessionEvents, setSessionEvents] = useState<SessionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sseError, setSseError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<RemoteAgent | null>(null);
  const [dashboardRefreshKey, setDashboardRefreshKey] = useState(0);

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
        <p>Loading control context...</p>
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
    <div className="control-panel">
      <header className="control-panel__header">
        <div>
          <h1>Control Panel</h1>
          <p>Real-time control observability and agent monitoring</p>
        </div>
      </header>

      <section className="control-panel__context">
        <div className="control-panel__context-card">
          <div className="control-panel__context-label">Control Context</div>
          <div className="control-panel__context-value">
            {controlSessionId ?? "Unavailable"}
          </div>
        </div>
        <div className="control-panel__context-card">
          <div className="control-panel__context-label">Selected Agent</div>
          <div className="control-panel__context-value">
            {selectedAgent
              ? `${selectedAgent.name} (${selectedAgent.agent_id})`
              : "None selected"}
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

      <section className="control-panel__layout">
        <aside className="control-panel__sidebar">
          <AgentConnectionDashboard
            key={dashboardRefreshKey}
            onSelectAgent={(agent) => setSelectedAgent(agent)}
            selectedAgentId={selectedAgent?.agent_id ?? null}
          />
          <AgentRegistrationPanel
            onRegistered={(agent) => {
              setSelectedAgent(agent);
              setDashboardRefreshKey((prev) => prev + 1);
            }}
          />
        </aside>

        <main className="control-panel__main">
          <TaskDispatchPanel
            agentId={selectedAgent?.agent_id ?? null}
            agentName={selectedAgent?.name}
            agentEvents={sessionEvents}
          />
          <StreamingOutputView agentId={selectedAgent?.agent_id ?? null} />
        </main>
      </section>

      <section className="control-panel__monitoring">
        <details className="control-panel__collapsible" open>
          <summary>Event Stream</summary>
          <EventStream
            events={sessionEvents}
            sessionId={controlSessionId}
            onClear={() => setSessionEvents([])}
          />
        </details>
        <details className="control-panel__collapsible">
          <summary>Cost Analytics</summary>
          <CostAnalytics events={sessionEvents} />
        </details>
      </section>
    </div>
  );
}
