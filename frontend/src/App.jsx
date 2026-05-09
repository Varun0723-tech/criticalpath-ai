import { useEffect, useState } from "react";

import AgentLogTimeline from "./components/AgentLogTimeline";
import AlertBanner from "./components/AlertBanner";
import ExplainabilityPanel from "./components/ExplainabilityPanel";
import JsonPanel from "./components/JsonPanel";
import LoadingWorkflow from "./components/LoadingWorkflow";
import RiskMeter from "./components/RiskMeter";
import SectionCard from "./components/SectionCard";
import SeverityBadge from "./components/SeverityBadge";

const PLACEHOLDER_SYMPTOMS = "chest pain, shortness of breath";
const DEMO_SYMPTOMS = ["chest pain", "sweating", "shortness of breath"];
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const LOADING_STEP_COUNT = 6;
const API_UNREACHABLE_MESSAGE =
  "Backend is unreachable. Start FastAPI on http://127.0.0.1:8000 and restart Vite if you changed frontend .env.";

function splitSymptoms(rawValue) {
  return rawValue
    .split(/,|\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function getErrorMessage(errorPayload) {
  if (!errorPayload) {
    return "Unable to process the case right now.";
  }

  if (typeof errorPayload.detail === "string") {
    return errorPayload.detail;
  }

  return "Unable to process the case right now.";
}

function getConfidenceTone(confidence = 0) {
  if (confidence >= 75) {
    return "high";
  }
  if (confidence >= 50) {
    return "medium";
  }
  return "low";
}

function buildApiCandidates() {
  const candidates = [];

  if (API_BASE_URL) {
    candidates.push(`${API_BASE_URL.replace(/\/$/, "")}/triage`);
  }

  candidates.push("/triage");
  return [...new Set(candidates)];
}

async function submitCase(payload) {
  let lastNetworkError = null;

  for (const apiPath of buildApiCandidates()) {
    try {
      const response = await fetch(apiPath, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(getErrorMessage(data));
      }

      return data;
    } catch (requestError) {
      if (requestError instanceof SyntaxError) {
        throw new Error("The backend returned an unreadable response. Restart the backend and try again.");
      }

      if (requestError instanceof TypeError) {
        lastNetworkError = requestError;
        continue;
      }

      throw requestError;
    }
  }

  throw new Error(lastNetworkError?.message === "Failed to fetch" ? API_UNREACHABLE_MESSAGE : lastNetworkError?.message || API_UNREACHABLE_MESSAGE);
}

export default function App() {
  const [age, setAge] = useState("");
  const [symptoms, setSymptoms] = useState(PLACEHOLDER_SYMPTOMS);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showJson, setShowJson] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [copyState, setCopyState] = useState("");

  useEffect(() => {
    setVoiceSupported(Boolean(window.SpeechRecognition || window.webkitSpeechRecognition));
  }, []);

  useEffect(() => {
    if (!loading) {
      setLoadingStep(0);
      return undefined;
    }

    setLoadingStep(0);
    const interval = window.setInterval(() => {
      setLoadingStep((current) => (current < LOADING_STEP_COUNT - 1 ? current + 1 : current));
    }, 550);

    return () => window.clearInterval(interval);
  }, [loading]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setReport(null);
    setShowJson(false);
    setCopyState("");

    const payload = {
      age: Number(age),
      symptoms: splitSymptoms(symptoms)
    };

    try {
      const data = await submitCase(payload);
      setReport(data);
    } catch (requestError) {
      setError(requestError.message || "Unable to process the case right now.");
    } finally {
      setLoading(false);
    }
  }

  function loadDemoCase() {
    setAge("52");
    setSymptoms(DEMO_SYMPTOMS.join(", "));
    setError("");
    setCopyState("");
  }

  function handleVoiceCapture() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setListening(true);
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript?.trim();
      if (transcript) {
        setSymptoms((current) => (current ? `${current}, ${transcript}` : transcript));
      }
    };

    recognition.start();
  }

  function downloadReport() {
    if (!report) {
      return;
    }

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `criticalpath-report-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function copySummary() {
    if (!report?.summary) {
      return;
    }

    try {
      await navigator.clipboard.writeText(report.summary);
      setCopyState("Summary copied");
      window.setTimeout(() => setCopyState(""), 1800);
    } catch {
      setCopyState("Clipboard unavailable");
      window.setTimeout(() => setCopyState(""), 1800);
    }
  }

  const symptomChips = splitSymptoms(symptoms);
  const severity = report?.triage?.triage_level;
  const isCritical = severity === "Critical";
  const redFlags = report?.explanation?.red_flags || report?.triage?.red_flags || [];

  return (
    <div className={`app-shell ${isCritical ? "has-critical-banner" : ""}`.trim()}>
      {isCritical ? (
        <AlertBanner
          tone="critical"
          icon="🚨"
          className="critical-ribbon"
          title="HIGH RISK PATIENT — IMMEDIATE ACTION REQUIRED"
          message={report.riskInterpretation}
        />
      ) : null}

      <header className="hero">
        <div className="hero-copy panel">
          <span className="eyebrow">Emergency Care Intelligence</span>
          <h1>CriticalPath AI</h1>
          <p>
            A hospital-style triage workspace that simulates intake, severity review, risk scoring,
            differential diagnosis, and structured reporting.
          </p>
        </div>
        <div className="hero-metrics panel">
          <div>
            <span className="metric-label">Workflow</span>
            <strong>6 specialized agents</strong>
          </div>
          <div>
            <span className="metric-label">Output</span>
            <strong>FHIR-style clinical bundle</strong>
          </div>
          <div>
            <span className="metric-label">Disposition</span>
            <strong>{severity || (loading ? "In progress" : "Awaiting case submission")}</strong>
          </div>
        </div>
      </header>

      <main className="dashboard-grid">
        <SectionCard title="Patient Intake" eyebrow="Input" className="form-card">
          <form onSubmit={handleSubmit} className="triage-form">
            <label>
              <span>Age</span>
              <input
                type="number"
                min="0"
                value={age}
                onChange={(event) => setAge(event.target.value)}
                placeholder="Enter age"
                required
              />
            </label>

            <label>
              <span>Symptoms</span>
              <textarea
                rows="5"
                value={symptoms}
                onChange={(event) => setSymptoms(event.target.value)}
                placeholder="Use commas to separate symptoms"
                required
              />
            </label>

            <div className="symptom-chip-row">
              {symptomChips.map((symptom) => (
                <span className="symptom-chip" key={symptom}>
                  {symptom}
                </span>
              ))}
            </div>

            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={loading}>
                {loading ? "Running multi-agent triage..." : "Run ER triage"}
              </button>
              <button className="secondary-button" type="button" onClick={loadDemoCase} disabled={loading}>
                Demo mode
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={handleVoiceCapture}
                disabled={!voiceSupported || listening || loading}
              >
                {listening ? "Listening..." : "Voice input"}
              </button>
            </div>

            {loading ? <div className="status-banner info">Agents are evaluating this case now.</div> : null}
            {error ? <div className="status-banner error">{error}</div> : null}
            {!voiceSupported ? <div className="status-banner muted">Voice input is not supported in this browser.</div> : null}
          </form>
        </SectionCard>

        <div className="results-column">
          <SectionCard title="Clinical Snapshot" eyebrow="Output">
            {loading ? (
              <LoadingWorkflow activeIndex={loadingStep} />
            ) : report ? (
              <div className="snapshot-grid">
                <div className={`snapshot-tile emphasis ${report.triage.triage_level.toLowerCase()}`}>
                  <span className="metric-label">Severity</span>
                  <SeverityBadge level={report.triage.triage_level} />
                  <p>{report.triage.reasoning}</p>
                </div>

                <div className="snapshot-tile">
                  <span className="metric-label">Red Flags</span>
                  <div className={`red-flag-box ${redFlags.length ? "active" : ""}`}>
                    {redFlags.length ? (
                      redFlags.map((flag) => (
                        <span className="flag-chip" key={flag}>
                          {flag}
                        </span>
                      ))
                    ) : (
                      <strong>No red flags detected</strong>
                    )}
                  </div>
                </div>

                <div className="snapshot-tile">
                  <RiskMeter score={report.riskAssessment.risk_score} level={report.riskAssessment.risk_level} />
                  <p>{report.riskInterpretation}</p>
                </div>

                <div className="snapshot-tile">
                  <span className="metric-label">Clinical Impression</span>
                  <p>{report.clinicalImpression}</p>
                </div>

                <div className="snapshot-tile">
                  <span className="metric-label">Summary</span>
                  <p>{report.summary}</p>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <h3>Awaiting a patient case</h3>
                <p>Submit age and symptoms to generate a full emergency care intelligence report.</p>
              </div>
            )}
          </SectionCard>

          <div className="dual-grid">
            <SectionCard title="Top Diagnoses" eyebrow="Differential">
              {report ? (
                <div className="diagnosis-list">
                  {report.condition.map((item) => {
                    const tone = getConfidenceTone(item.confidence);
                    return (
                      <article className={`diagnosis-card ${tone}`} key={item.name || item.condition}>
                        <div className="diagnosis-header">
                          <strong>{item.name || item.condition}</strong>
                          <span className={`confidence-pill ${tone}`}>{item.confidence}% confidence</span>
                        </div>
                        <div className="confidence-track">
                          <div className={`confidence-fill ${tone}`} style={{ width: `${item.confidence}%` }} />
                        </div>
                        <p>{item.reason}</p>
                      </article>
                    );
                  })}
                </div>
              ) : (
                <p className="placeholder-copy">Differential diagnoses will appear here.</p>
              )}
            </SectionCard>

            <SectionCard title="Care Plan" eyebrow="Recommendation">
              {report ? (
                <div className="care-plan">
                  <div className="care-callout">
                    <span className="metric-label">Recommended Action</span>
                    <strong>{report.carePlan.recommended_action}</strong>
                    <p>{report.carePlan.notes}</p>
                  </div>
                  <div className="care-meta">
                    <div>
                      <span className="metric-label">Urgency</span>
                      <strong>{report.carePlan.urgency}</strong>
                    </div>
                    <div>
                      <span className="metric-label">Suggested Tests</span>
                      <p>{report.carePlan.tests.length ? report.carePlan.tests.join(", ") : "None suggested"}</p>
                    </div>
                    <div>
                      <span className="metric-label">Monitoring Advice</span>
                      <p>{report.carePlan.monitoring_advice.length ? report.carePlan.monitoring_advice.join(" ") : "No extra monitoring advice."}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="placeholder-copy">Disposition guidance will appear here.</p>
              )}
            </SectionCard>
          </div>

          <div className="dual-grid">
            <SectionCard title="Agent Workflow" eyebrow="Observability">
              {loading ? (
                <LoadingWorkflow activeIndex={loadingStep} />
              ) : report ? (
                <AgentLogTimeline logs={report.agentLogs} />
              ) : (
                <p className="placeholder-copy">Agent logs will appear once a case is processed.</p>
              )}
            </SectionCard>

            <SectionCard title="Why this decision was made" eyebrow="🧠 Explainability">
              <ExplainabilityPanel
                explanation={report?.explanation}
                explainability={report?.explainability}
                riskFactors={report?.riskAssessment?.weighted_factors}
              />
            </SectionCard>
          </div>

          <SectionCard title="Structured Report" eyebrow="FHIR JSON">
            {report ? (
              <>
                <JsonPanel open={showJson} onToggle={() => setShowJson((current) => !current)} data={report} />
                <div className="action-row">
                  <button className="secondary-button wide" type="button" onClick={downloadReport}>
                    Download report as JSON
                  </button>
                  <button className="secondary-button wide" type="button" onClick={copySummary}>
                    Copy summary
                  </button>
                  {copyState ? <span className="copy-feedback">{copyState}</span> : null}
                </div>
              </>
            ) : (
              <p className="placeholder-copy">FHIR-style output will be rendered here.</p>
            )}
          </SectionCard>
        </div>
      </main>
    </div>
  );
}
