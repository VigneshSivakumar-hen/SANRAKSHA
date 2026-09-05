import { useEffect, useState } from "react";
import { fetchHistory } from "../services/api";

const W = 260;
const H = 56;
const PAD = 4;

export default function HistorySparkline({ locationId }) {
  const [entries, setEntries] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error | empty

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setEntries(null);

    fetchHistory(locationId)
      .then((data) => {
        if (cancelled) return;
        if (!data || data.length < 2) {
          setStatus("empty");
          return;
        }
        // Oldest first, so the line reads left-to-right chronologically.
        setEntries([...data].reverse());
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [locationId]);

  if (status === "loading") {
    return <SparklinePlaceholder text="Loading trend…" />;
  }
  if (status === "error") {
    return <SparklinePlaceholder text="Trend unavailable" />;
  }
  if (status === "empty") {
    return <SparklinePlaceholder text="Not enough history yet" />;
  }

  const scores = entries.map((e) => e.risk_score);
  const min = Math.min(...scores);
  const max = Math.max(...scores);
  const range = max - min || 1;

  const points = entries.map((e, i) => {
    const x = PAD + (i / (entries.length - 1)) * (W - PAD * 2);
    const y = H - PAD - ((e.risk_score - min) / range) * (H - PAD * 2);
    return [x, y];
  });

  const linePath = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${points[points.length - 1][0].toFixed(1)},${H - PAD} L${points[0][0].toFixed(1)},${H - PAD} Z`;

  const latest = entries[entries.length - 1];
  const earliest = entries[0];
  const trend = latest.risk_score - earliest.risk_score;

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-label="Risk score trend over recent readings">
        <path d={areaPath} fill="var(--risk-moderate)" opacity="0.08" />
        <path d={linePath} fill="none" stroke="var(--risk-moderate)" strokeWidth="1.5" />
        {points.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={i === points.length - 1 ? 2.5 : 1.5} fill="var(--risk-moderate)" />
        ))}
      </svg>
      <p style={{ fontSize: 11, color: "var(--text-muted)", margin: "4px 0 0", fontFamily: "var(--font-mono)" }}>
        {trend > 0 ? "▲" : trend < 0 ? "▼" : "—"} {Math.abs(trend).toFixed(0)} pts over last {entries.length} readings
      </p>
    </div>
  );
}

function SparklinePlaceholder({ text }) {
  return (
    <div
      style={{
        width: W,
        height: H,
        display: "flex",
        alignItems: "center",
        color: "var(--text-muted)",
        fontSize: 12,
      }}
    >
      {text}
    </div>
  );
}
