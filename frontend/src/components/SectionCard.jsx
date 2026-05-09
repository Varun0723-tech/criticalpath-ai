export default function SectionCard({ title, eyebrow, children, className = "" }) {
  return (
    <section className={`section-card ${className}`.trim()}>
      {(eyebrow || title) && (
        <div className="section-heading">
          {eyebrow ? <span className="section-eyebrow">{eyebrow}</span> : null}
          {title ? <h2>{title}</h2> : null}
        </div>
      )}
      {children}
    </section>
  );
}

