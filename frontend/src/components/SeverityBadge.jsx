const LABEL_MAP = {
  Critical: "critical",
  Urgent: "urgent",
  Normal: "normal"
};

export default function SeverityBadge({ level }) {
  const tone = LABEL_MAP[level] || "normal";

  return (
    <span className={`severity-badge ${tone}`}>
      <span className="severity-dot" />
      {level || "Pending"}
    </span>
  );
}

