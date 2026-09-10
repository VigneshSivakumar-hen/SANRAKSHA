export default function StateDistribution({ readings }) {
  const counts = {};
  for (const r of readings) {
    counts[r.state] = (counts[r.state] || 0) + 1;
  }
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const max = Math.max(...entries.map(([, n]) => n), 1);

  if (entries.length === 0) return null;

  return (
    <div style={{ marginTop: 20 }}>
      <p style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: 0.4, margin: "0 0 10px" }}>
        LOCATIONS BY STATE
      </p>
      {entries.map(([state, count]) => (
        <div key={state} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 12, width: 100, flexShrink: 0, color: "var(--text)" }}>{state}</span>
          <div style={{ flex: 1, background: "var(--panel-raised)", borderRadius: 2, height: 6 }}>
            <div
              style={{
                width: `${(count / max) * 100}%`,
                background: "var(--text-muted)",
                height: "100%",
                borderRadius: 2,
              }}
            />
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-muted)", width: 14, textAlign: "right" }}>
            {count}
          </span>
        </div>
      ))}
    </div>
  );
}
