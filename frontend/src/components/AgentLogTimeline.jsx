const AGENT_ICONS = {
  "Intake Agent": "📝",
  "Triage Agent": "🚨",
  "Diagnosis Agent": "🧠",
  "Risk Agent": "📊",
  "Recommendation Agent": "💊",
  "Report Agent": "📄"
};

const STATUS_META = {
  processing: { icon: "⏳", label: "Processing" },
  completed: { icon: "✅", label: "Completed" },
  fallback: { icon: "⚠️", label: "Fallback used" }
};

export default function AgentLogTimeline({ logs = [] }) {
  const visibleLogs = logs.filter((log) => log.status !== "fallback");

  return (
    <div className="timeline">
      {visibleLogs.map((log, index) => {
        const status = STATUS_META[log.status] || STATUS_META.completed;
        return (
          <article className={`timeline-item ${log.status}`} key={`${log.agent}-${log.timestamp}-${index}`}>
            <div className="timeline-marker">
              <span>{AGENT_ICONS[log.agent] || "•"}</span>
            </div>
            <div className="timeline-content">
              <div className="timeline-header">
                <strong>{log.agent}</strong>
                <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="timeline-status-row">
                <span className={`timeline-status ${log.status}`}>
                  {status.icon} {status.label}
                </span>
              </div>
              <p>{log.message}</p>
              {log.details ? <small>{log.details}</small> : null}
            </div>
          </article>
        );
      })}
    </div>
  );
}
