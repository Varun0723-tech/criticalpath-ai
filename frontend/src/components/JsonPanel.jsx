export default function JsonPanel({ open, onToggle, data }) {
  return (
    <div className="json-panel">
      <button className="ghost-button" type="button" onClick={onToggle}>
        {open ? "Hide structured report" : "View structured report"}
      </button>
      {open ? <pre>{JSON.stringify(data, null, 2)}</pre> : null}
    </div>
  );
}

