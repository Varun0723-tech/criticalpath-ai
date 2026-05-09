export default function RiskMeter({ score = 0, level = "Low" }) {
  return (
    <div className="risk-meter">
      <div className="risk-meter-header">
        <div>
          <p className="metric-label">Risk Score</p>
          <strong>{score}/100</strong>
        </div>
        <span className={`risk-pill ${level.toLowerCase()}`}>{level}</span>
      </div>
      <div className="progress-track" aria-label={`Risk score ${score} out of 100`}>
        <div className="progress-fill" style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

