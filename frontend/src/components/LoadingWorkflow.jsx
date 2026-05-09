const AGENT_STEPS = [
  { agent: "Intake Agent", icon: "📝", detail: "Validating age and normalizing symptoms" },
  { agent: "Triage Agent", icon: "🚨", detail: "Checking red flags and acuity" },
  { agent: "Diagnosis Agent", icon: "🧠", detail: "Building a focused differential" },
  { agent: "Risk Agent", icon: "📊", detail: "Scoring severity and weighted risk" },
  { agent: "Recommendation Agent", icon: "💊", detail: "Preparing tests and disposition" },
  { agent: "Report Agent", icon: "📄", detail: "Assembling the structured report" }
];

export default function LoadingWorkflow({ activeIndex = 0 }) {
  return (
    <div className="loading-workflow">
      <div className="loader-orbit" />
      <div className="loading-copy">
        <strong>Agents are processing this case</strong>
        <p>Simulating a real ER workflow while the clinical report is assembled.</p>
      </div>
      <div className="workflow-preview">
        {AGENT_STEPS.map((step, index) => {
          const state = index < activeIndex ? "completed" : index === activeIndex ? "processing" : "queued";
          const stateLabel = state === "completed" ? "Completed" : state === "processing" ? "Processing" : "Queued";
          const statusIcon = state === "completed" ? "✅" : state === "processing" ? "⏳" : "•";

          return (
            <article className={`workflow-step ${state}`} key={step.agent}>
              <div className="workflow-step-icon">{step.icon}</div>
              <div>
                <div className="workflow-step-header">
                  <strong>{step.agent}</strong>
                  <span>{statusIcon} {stateLabel}</span>
                </div>
                <p>{step.detail}</p>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

