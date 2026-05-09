function formatFactorChip(label) {
  return (
    <div className="factor-chip" key={label}>
      <span>{label}</span>
    </div>
  );
}

export default function ExplainabilityPanel({ explanation, explainability, riskFactors }) {
  if (!explanation && !explainability) {
    return <p className="placeholder-copy">Clinical reasoning will appear here.</p>;
  }

  const redFlags = explanation?.red_flags || [];
  const riskItems = explanation?.risk_factors || [];

  const factorEntries = riskFactors
    ? [
        `Baseline +${riskFactors.baseline}`,
        `Red flags +${riskFactors.red_flags}`,
        `Age +${riskFactors.age}`,
        `Severe symptoms +${riskFactors.severe_symptoms}`,
        `Triage +${riskFactors.triage}`,
        `Symptom burden +${riskFactors.symptom_burden}`
      ]
    : [];

  return (
    <div className="explainability-panel">
      <article className="explain-card">
        <span className="metric-label">🚩 Red Flags Detected</span>
        {redFlags.length ? (
          <div className="factor-row">
            {redFlags.map((flag) => (
              <span className="flag-chip" key={flag}>
                {flag}
              </span>
            ))}
          </div>
        ) : (
          <p>No rule-based red flags were identified.</p>
        )}
      </article>

      <article className="explain-card">
        <span className="metric-label">⚙️ Clinical Reasoning</span>
        <p>{explanation?.reasoning || explainability?.triage_decision}</p>
      </article>

      <article className="explain-card">
        <span className="metric-label">📊 Risk Explanation</span>
        <p>{explainability?.risk_rationale}</p>
        {riskItems.length ? (
          <div className="risk-factor-list">
            {riskItems.map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        ) : null}
      </article>

      <article className="explain-card">
        <span className="metric-label">🧠 Diagnostic Context</span>
        <p>{explainability?.diagnostic_rationale}</p>
      </article>

      {factorEntries.length ? <div className="factor-row">{factorEntries.map((item) => formatFactorChip(item))}</div> : null}
    </div>
  );
}
