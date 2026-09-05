const RISK_COLOR = {
  LOW: "var(--risk-low)",
  MODERATE: "var(--risk-moderate)",
  HIGH: "var(--risk-high)",
  CRITICAL: "var(--risk-critical)",
};

const LEVELS = ["CRITICAL", "HIGH", "MODERATE", "LOW"];

export default function SummaryStrip({ readings }) {
  const counts = Object.fromEntries(LEVELS.map((l) => [l, 0]));
  for (const r of readings) {
    if (counts[r.risk_level] !== undefined) counts[r.risk_level] += 1;
  }

  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
      {LEVELS.map((level) => (
        <div
          key={level}
          style={{
            background: "var(--panel)",
            border: "1px solid var(--line)",
            borderTop: `2px solid ${RISK_COLOR[level]}`,
            borderRadius: 4,
            padding: "10px 16px",
            minWidth: 100,
          }}
        >
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 22, color: RISK_COLOR[level] }}>
            {counts[level]}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: 0.4 }}>{level}</div>
        </div>
      ))}
    </div>
  );
}
