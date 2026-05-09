export default function AlertBanner({ tone = "info", title, message, icon, className = "" }) {
  const resolvedIcon = icon || (tone === "critical" ? "🚨" : tone === "warning" ? "⚠️" : "ℹ️");

  return (
    <div className={`alert-banner ${tone} ${className}`.trim()}>
      <div className="alert-banner-icon">{resolvedIcon}</div>
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
      </div>
    </div>
  );
}

