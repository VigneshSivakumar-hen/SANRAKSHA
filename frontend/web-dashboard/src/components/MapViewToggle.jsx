const OPTIONS = [
  { value: "satellite", label: "Satellite" },
  { value: "schematic", label: "Schematic" },
];

export default function MapViewToggle({ value, onChange }) {
  return (
    <div
      style={{
        display: "inline-flex",
        border: "1px solid var(--line)",
        borderRadius: 4,
        overflow: "hidden",
        marginBottom: 10,
      }}
      role="tablist"
      aria-label="Map view"
    >
      {OPTIONS.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(opt.value)}
            style={{
              background: active ? "var(--panel-raised)" : "var(--panel)",
              color: active ? "var(--text)" : "var(--text-muted)",
              border: "none",
              padding: "6px 14px",
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              cursor: "pointer",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
