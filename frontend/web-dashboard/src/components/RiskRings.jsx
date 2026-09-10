const RISK_COLOR = {
  CRITICAL: "var(--risk-critical)",
  HIGH: "var(--risk-high)",
  MODERATE: "var(--risk-moderate)",
  LOW: "var(--risk-low)",
};

const LEVELS = ["CRITICAL", "HIGH", "MODERATE", "LOW"];
const R = 26;
const CIRCUMFERENCE = 2 * Math.PI * R;

export default function RiskRings({ readings }) {
  const total = readings.length || 1;
  const counts = Object.fromEntries(LEVELS.map((l) => [l, 0]));
  for (const r of readings) {
    if (counts[r.risk_level] !== undefined) counts[r.risk_level] += 1;
  }

  return (
    <div style={{ display: "flex", gap: 22, flexWrap: "wrap" }}>
      {LEVELS.map((level) => {
        const count = counts[level];
        const color = RISK_COLOR[level];
        const fraction = count / total;
        const dash = `${(fraction * CIRCUMFERENCE).toFixed(1)} ${CIRCUMFERENCE.toFixed(1)}`;

        return (
          <div key={level} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
            <svg width="64" height="64" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r={R} fill="none" stroke="var(--line)" strokeWidth="4" />
              {count > 0 && (
                <circle
                  cx="32"
                  cy="32"
                  r={R}
                  fill="none"
                  stroke={color}
                  strokeWidth="4"
                  strokeDasharray={dash}
                  strokeLinecap="round"
                  transform="rotate(-90 32 32)"
                />
              )}
              <text
                x="32"
                y="37"
                textAnchor="middle"
                fontFamily="var(--font-mono)"
                fontSize="20"
                fill={count > 0 ? color : "var(--text-muted)"}
              >
                {count}
              </text>
            </svg>
            <span style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: 0.4 }}>{level}</span>
          </div>
        );
      })}
    </div>
  );
}
