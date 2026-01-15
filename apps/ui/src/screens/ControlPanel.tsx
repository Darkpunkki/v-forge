import { useEffect, useState } from "react";
import {
  listAllSessions,
  getActiveSessions,
  getSessionStatus,
  streamSessionEvents,
  getWorkflowConfig,
  getSimulationState,
  type SessionListItem,
  type ActiveSessionItem,
  type SessionStatusResponse,
  type SessionEvent,
  type WorkflowConfigResponse,
  type SimulationStateResponse,
} from "../api/controlClient";
import AgentDashboard from "./control/widgets/AgentDashboard";
import AgentGraph from "./control/widgets/AgentGraph";
import ExecutionTimeline from "./control/widgets/ExecutionTimeline";
import EventStream from "./control/widgets/EventStream";
import GateLog from "./control/widgets/GateLog";
import ModelRouter from "./control/widgets/ModelRouter";
import PromptInspector from "./control/widgets/PromptInspector";
import SessionComparison from "./control/widgets/SessionComparison";
import TokenVisualization from "./control/widgets/TokenVisualization";
import CostAnalytics from "./control/widgets/CostAnalytics";
import { AgentInitializer } from "./control/widgets/AgentInitializer";
import { AgentAssignment } from "./control/widgets/AgentAssignment";
import { AgentTaskInput } from "./control/widgets/AgentTaskInput";
import { AgentFlowEditor } from "./control/widgets/AgentFlowEditor";
import { SimulationConfig } from "./control/widgets/SimulationConfig";
import { TickControls } from "./control/widgets/TickControls";
import MultiAgentMessages from "./control/widgets/MultiAgentMessages";

export function ControlPanelScreen() {
  const [allSessions, setAllSessions] = useState<SessionListItem[]>([]);
  const [activeSessions, setActiveSessions] = useState<ActiveSessionItem[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  );
  const [sessionStatus, setSessionStatus] =
    useState<SessionStatusResponse | null>(null);
  const [sessionEvents, setSessionEvents] = useState<SessionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSession, setLoadingSession] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sseError, setSseError] = useState<string | null>(null);
  const [workflowConfig, setWorkflowConfig] = useState<WorkflowConfigResponse | null>(null);
  const [simulationState, setSimulationState] = useState<SimulationStateResponse | null>(null);
  const [initialPrompt, setInitialPrompt] = useState<string>("");
  const [firstAgentId, setFirstAgentId] = useState<string>("");
  const artifactKeys = ["concept", "build_spec", "task_graph"];

  const getArtifactCount = (session: SessionListItem, key: string) =>
    session.artifacts.filter((artifact) => artifact === key).length;

  // Load all sessions and active sessions on mount
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [allData, activeData] = await Promise.all([
          listAllSessions(),
          getActiveSessions(),
        ]);
        setAllSessions(allData.sessions);
        setActiveSessions(activeData.active_sessions);
      } catch (err: any) {
        setError(err?.detail || err?.message || String(err));
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Load session status and events when a session is selected
  useEffect(() => {
    if (!selectedSessionId) {
      setSessionStatus(null);
      setSessionEvents([]);
      setSseError(null);
      setWorkflowConfig(null);
      setSimulationState(null);
      setInitialPrompt("");
      setFirstAgentId("");
      setLoadingSession(false);
      return;
    }

    // Clear events immediately when switching sessions
    setSessionEvents([]);
    setSseError(null);
    setLoadingSession(true);

    // Capture sessionId to fix TypeScript null error and prevent race conditions
    const sessionId = selectedSessionId;
    let cancelled = false;

    async function loadSessionDetails() {
      try {
        const [status, workflow, simState] = await Promise.all([
          getSessionStatus(sessionId),
          getWorkflowConfig(sessionId).catch(() => null), // Workflow config is optional
          getSimulationState(sessionId).catch(() => null), // Simulation state is optional
        ]);
        if (!cancelled) {
          setSessionStatus(status);
          setWorkflowConfig(workflow);
          setSimulationState(simState);
          setLoadingSession(false);
        }
      } catch (err: any) {
        console.error("Failed to load session details:", err);
        if (!cancelled) {
          setLoadingSession(false);
        }
      }
    }

    loadSessionDetails();

    // Set up SSE for real-time events
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
  }, [selectedSessionId]);

  useEffect(() => {
    if (!simulationState) {
      return;
    }
    if (simulationState.initial_prompt !== null && simulationState.initial_prompt !== undefined) {
      setInitialPrompt(simulationState.initial_prompt);
    }
    if (simulationState.first_agent_id !== null && simulationState.first_agent_id !== undefined) {
      setFirstAgentId(simulationState.first_agent_id);
    }
  }, [simulationState?.initial_prompt, simulationState?.first_agent_id]);

  // Handler to refresh workflow configuration
  const refreshWorkflowConfig = async () => {
    if (!selectedSessionId) return;
    try {
      const workflow = await getWorkflowConfig(selectedSessionId);
      setWorkflowConfig(workflow);
    } catch (err) {
      console.error("Failed to refresh workflow config:", err);
    }
  };

  // Handler to refresh simulation state
  const refreshSimulationState = async () => {
    if (!selectedSessionId) return;
    try {
      const simState = await getSimulationState(selectedSessionId);
      setSimulationState(simState);
    } catch (err) {
      console.error("Failed to refresh simulation state:", err);
    }
  };

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
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: "300px",
          borderRight: "1px solid #ddd",
          padding: "16px",
          overflowY: "auto",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Sessions</h2>

        <section style={{ marginBottom: "24px" }}>
          <h3
            style={{
              fontSize: "14px",
              opacity: 0.7,
              textTransform: "uppercase",
            }}
          >
            Active ({activeSessions.length})
          </h3>
          {activeSessions.length === 0 ? (
            <p style={{ fontSize: "14px", opacity: 0.6 }}>No active sessions</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {activeSessions.map((session) => (
                <li
                  key={session.session_id}
                  style={{
                    padding: "8px",
                    marginBottom: "4px",
                    background:
                      selectedSessionId === session.session_id
                        ? "#e3f2fd"
                        : "#f5f5f5",
                    cursor: "pointer",
                    borderRadius: "4px",
                  }}
                  onClick={() => setSelectedSessionId(session.session_id)}
                >
                  <div style={{ fontSize: "12px", fontWeight: "bold" }}>
                    {session.session_id}
                  </div>
                  <div style={{ fontSize: "11px", opacity: 0.7 }}>
                    {session.phase}
                  </div>
                  <div style={{ fontSize: "11px", opacity: 0.7 }}>
                    Active task: {session.active_task_id || "—"}
                  </div>
                  <div style={{ fontSize: "10px", opacity: 0.5 }}>
                    Updated {new Date(session.updated_at).toLocaleString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h3
            style={{
              fontSize: "14px",
              opacity: 0.7,
              textTransform: "uppercase",
            }}
          >
            All Sessions ({allSessions.length})
          </h3>
          {allSessions.length === 0 ? (
            <p style={{ fontSize: "14px", opacity: 0.6 }}>No sessions found</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {allSessions.map((session) => (
                <li
                  key={session.session_id}
                  style={{
                    padding: "8px",
                    marginBottom: "4px",
                    background:
                      selectedSessionId === session.session_id
                        ? "#e3f2fd"
                        : "#f5f5f5",
                    cursor: "pointer",
                    borderRadius: "4px",
                  }}
                  onClick={() => setSelectedSessionId(session.session_id)}
                >
                  <div style={{ fontSize: "12px", fontWeight: "bold" }}>
                    {session.session_id}
                  </div>
                  <div style={{ fontSize: "11px", opacity: 0.7 }}>
                    {session.phase || "Unknown"}
                  </div>
                  <div style={{ fontSize: "10px", opacity: 0.5 }}>
                    {new Date(session.updated_at).toLocaleString()}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: "6px",
                      flexWrap: "wrap",
                      marginTop: "6px",
                    }}
                  >
                    {artifactKeys.map((key) => {
                      const count = getArtifactCount(session, key);
                      return (
                        <span
                          key={key}
                          style={{
                            fontSize: "10px",
                            padding: "2px 6px",
                            borderRadius: "999px",
                            background: count > 0 ? "#e3f2fd" : "#eee",
                            color: count > 0 ? "#1565c0" : "#666",
                            border:
                              count > 0
                                ? "1px solid #90caf9"
                                : "1px solid #ddd",
                          }}
                        >
                          {key} · {count}
                        </span>
                      );
                    })}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, padding: "24px", overflowY: "auto" }}>
        <header style={{ marginBottom: "24px" }}>
          <h1 style={{ marginTop: 0 }}>Control Panel</h1>
          <p style={{ opacity: 0.7 }}>
            Real-time session monitoring and observability
          </p>
        </header>

        {!selectedSessionId ? (
          <div style={{ padding: "48px", textAlign: "center", opacity: 0.6 }}>
            <p>Select a session from the sidebar to view details</p>
          </div>
        ) : (
          <>
            {/* SSE Error Notification */}
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
                <span>⚠️</span>
                <span>{sseError}</span>
              </div>
            )}

            {/* Loading State */}
            {loadingSession ? (
              <div
                style={{ padding: "48px", textAlign: "center", opacity: 0.6 }}
              >
                <p>Loading session details...</p>
              </div>
            ) : (
              <>
                {/* Session Status */}
                {sessionStatus && (
                  <section style={{ marginBottom: "24px" }}>
                    <h2>Session Status</h2>
                    <div
                      style={{
                        background: "#f5f5f5",
                        padding: "16px",
                        borderRadius: "8px",
                        display: "grid",
                        gridTemplateColumns:
                          "repeat(auto-fit, minmax(200px, 1fr))",
                        gap: "16px",
                      }}
                    >
                      <div>
                        <div
                          style={{
                            fontSize: "12px",
                            opacity: 0.7,
                            textTransform: "uppercase",
                          }}
                        >
                          Session ID
                        </div>
                        <div style={{ fontWeight: "bold" }}>
                          {sessionStatus.session_id}
                        </div>
                      </div>
                      <div>
                        <div
                          style={{
                            fontSize: "12px",
                            opacity: 0.7,
                            textTransform: "uppercase",
                          }}
                        >
                          Phase
                        </div>
                        <div style={{ fontWeight: "bold" }}>
                          {sessionStatus.phase}
                        </div>
                      </div>
                      <div>
                        <div
                          style={{
                            fontSize: "12px",
                            opacity: 0.7,
                            textTransform: "uppercase",
                          }}
                        >
                          Active Task
                        </div>
                        <div style={{ fontWeight: "bold" }}>
                          {sessionStatus.active_task_id || "—"}
                        </div>
                      </div>
                      <div>
                        <div
                          style={{
                            fontSize: "12px",
                            opacity: 0.7,
                            textTransform: "uppercase",
                          }}
                        >
                          Completed Tasks
                        </div>
                        <div style={{ fontWeight: "bold" }}>
                          {sessionStatus.completed_tasks}
                        </div>
                      </div>
                      <div>
                        <div
                          style={{
                            fontSize: "12px",
                            opacity: 0.7,
                            textTransform: "uppercase",
                          }}
                        >
                          Failed Tasks
                        </div>
                        <div
                          style={{
                            fontWeight: "bold",
                            color:
                              sessionStatus.failed_tasks > 0
                                ? "#d32f2f"
                                : "inherit",
                          }}
                        >
                          {sessionStatus.failed_tasks}
                        </div>
                      </div>
                      <div>
                        <div
                          style={{
                            fontSize: "12px",
                            opacity: 0.7,
                            textTransform: "uppercase",
                          }}
                        >
                          Updated At
                        </div>
                        <div style={{ fontSize: "14px" }}>
                          {new Date(sessionStatus.updated_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </section>
                )}

                {/* Workflow Configuration Section (VF-195-198) */}
                <section style={{ marginBottom: "24px" }}>
                  <h2>Workflow Configuration</h2>
                  {!workflowConfig?.agents || workflowConfig.agents.length === 0 ? (
                    <AgentInitializer
                      sessionId={selectedSessionId}
                      onInitialized={refreshWorkflowConfig}
                    />
                  ) : (
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
                        gap: "16px",
                      }}
                    >
                      <AgentAssignment
                        sessionId={selectedSessionId}
                        agents={workflowConfig.agents}
                        availableRoles={simulationState?.available_roles}
                        onAssigned={refreshWorkflowConfig}
                      />
                      <AgentTaskInput
                        sessionId={selectedSessionId}
                        currentTask={workflowConfig.main_task || undefined}
                        onTaskSet={refreshWorkflowConfig}
                      />
                      <AgentFlowEditor
                        sessionId={selectedSessionId}
                        agents={workflowConfig.agents}
                        existingEdges={workflowConfig.agent_graph?.edges || []}
                        onFlowConfigured={refreshWorkflowConfig}
                      />
                    </div>
                  )}
                </section>

                {/* Simulation Control Section (VF-204) */}
                {workflowConfig?.agents && workflowConfig.agents.length > 0 && (
                  <section style={{ marginBottom: "24px" }}>
                    <h2>Simulation Control</h2>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
                        gap: "16px",
                      }}
                    >
                      <SimulationConfig
                        sessionId={selectedSessionId}
                        currentMode={simulationState?.simulation_mode}
                        currentDelayMs={simulationState?.auto_delay_ms}
                        currentTickBudget={simulationState?.tick_budget}
                        agents={workflowConfig?.agents || []}
                        initialPrompt={initialPrompt}
                        firstAgentId={firstAgentId}
                        onStartContextChange={(context) => {
                          setInitialPrompt(context.initialPrompt);
                          setFirstAgentId(context.firstAgentId);
                        }}
                        onConfigured={refreshSimulationState}
                      />
                      <TickControls
                        sessionId={selectedSessionId}
                        initialPrompt={initialPrompt}
                        firstAgentId={firstAgentId}
                        onStateChange={refreshSimulationState}
                      />
                    </div>
                  </section>
                )}

                {/* Monitoring Widgets */}
                <section>
                  <h2>Session Monitoring</h2>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
                      gap: "16px",
                    }}
                  >
                    <MultiAgentMessages events={sessionEvents} />
                    <AgentDashboard events={sessionEvents} />
                  <TokenVisualization events={sessionEvents} />
                  <AgentGraph events={sessionEvents} />
                  <ExecutionTimeline events={sessionEvents} />
                  <GateLog events={sessionEvents} />
                  <ModelRouter events={sessionEvents} />
                  <SessionComparison
                    sessions={allSessions}
                    selectedSessionId={selectedSessionId}
                  />
                  <EventStream
                    events={sessionEvents}
                    sessionId={selectedSessionId}
                    onClear={() => setSessionEvents([])}
                  />
                  <PromptInspector sessionId={selectedSessionId} />
                  <CostAnalytics events={sessionEvents} />
                  </div>
                </section>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
