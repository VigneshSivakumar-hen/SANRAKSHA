import { useEffect, useState } from "react";
import { fetchHistory } from "../services/api";

const RISK_COLOR = {
  LOW: "var(--risk-low)",
  MODERATE: "var(--risk-moderate)",
  HIGH: "var(--risk-high)",
  CRITICAL: "var(--risk-critical)",
};

const MAX_EVENTS = 14;

export default function ActivityFeed({ readings, refreshKey, onSelect }) {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  useEffect(() => {
    if (readings.length === 0) return;
    let cancelled = false;

    Promise.all(
      readings.map((r) =>
        fetchHistory(r.location_id)
          .then((entries) => entries.map((e) => ({ ...e, location_id: r.location_id, location_name: r.location_name })))
          .catch(() => [])
      )
    )
      .then((lists) => {
        if (cancelled) return;
        const merged = lists
          .flat()
          .sort((a, b) => new Date(b.recorded_at) - new Date(a.recorded_at))
          .slice(0, MAX_EVENTS);
        setEvents(merged);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
    // refreshKey (tied to the app-level poll) intentionally re-triggers this
    // without needing its own separate timer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readings.length, refreshKey]);

  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--line)",
        borderRadius: 4,
        padding: "16px 18px",
      }}
    >
      <p style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: 0.4, margin: "0 0 12px" }}>
        RECENT ACTIVITY
      </p>

      {status === "loading" && events.length === 0 && (
        <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading recent readings…</p>
      )}
      {status === "error" && (
        <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Activity feed unavailable right now.</p>
      )}
      {status === "ready" && events.length === 0 && (
        <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No readings recorded yet.</p>
      )}

      <div style={{ maxHeight: 480, overflowY: "auto" }}>
        {events.map((e, i) => (
          <button
            key={`${e.location_id}-${e.recorded_at}-${i}`}
            onClick={() => onSelect(e.location_id)}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              background: "none",
              border: "none",
              borderBottom: i < events.length - 1 ? "1px solid var(--line)" : "none",
              padding: "9px 0",
              cursor: "pointer",
              color: "var(--text)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: RISK_COLOR[e.risk_level] ?? "var(--text-muted)",
                  flexShrink: 0,
                }}
              />
              <span style={{ fontSize: 13 }}>{e.location_name}</span>
              <span
                style={{
                  marginLeft: "auto",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  color: RISK_COLOR[e.risk_level] ?? "var(--text-muted)",
                }}
              >
                {e.risk_score.toFixed(0)}
              </span>
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: 13, marginTop: 1 }}>
              {e.risk_level} · {relativeTime(e.recorded_at)}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function relativeTime(isoString) {
  const seconds = Math.round((Date.now() - new Date(isoString).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}
