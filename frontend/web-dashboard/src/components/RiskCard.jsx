const RISK_COLOR = {
  LOW: "var(--risk-low)",
  MODERATE: "var(--risk-moderate)",
  HIGH: "var(--risk-high)",
  CRITICAL: "var(--risk-critical)",
};

export default function RiskCard({ reading, selected, onSelect }) {
  const color = RISK_COLOR[reading.risk_level] ?? "var(--text-muted)";

  return (
    <button
      onClick={() => onSelect(reading.location_id)}
      style={{
        display: "block",
        width: "100%",
        textAlign: "left",
        background: selected ? "var(--panel-raised)" : "var(--panel)",
        border: "1px solid var(--line)",
        borderLeft: `3px solid ${color}`,
        borderRadius: 4,
        padding: "12px 14px",
        marginBottom: 8,
        cursor: "pointer",
        color: "var(--text)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span style={{ fontFamily: "var(--font-display)", fontSize: 16 }}>
          {reading.location_name}
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, color }}>
          {reading.risk_score.toFixed(0)}
        </span>
      </div>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
        {reading.state}
      </div>
      <div
        style={{
          display: "inline-block",
          marginTop: 8,
          fontSize: 11,
          fontFamily: "var(--font-mono)",
          color,
          border: `1px solid ${color}`,
          borderRadius: 3,
          padding: "2px 6px",
        }}
      >
        {reading.risk_level}
      </div>
    </button>
  );
}
