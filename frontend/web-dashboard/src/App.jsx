import { useEffect, useRef, useState } from "react";
import { fetchDashboard } from "./services/api";
import Dashboard from "./pages/Dashboard";
import "./styles/dashboard.css";

const POLL_INTERVAL_MS = 60_000;

export default function App() {
  const [readings, setReadings] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [lastUpdated, setLastUpdated] = useState(null);
  const [, forceTick] = useState(0);
  const hasLoadedOnce = useRef(false);

  // Re-render periodically so "Updated Xs ago" stays accurate between polls.
  useEffect(() => {
    const tick = setInterval(() => forceTick((n) => n + 1), 15_000);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchDashboard();
        if (cancelled) return;
        setReadings(data);
        setStatus("ready");
        setLastUpdated(new Date());
      } catch {
        if (!cancelled) setStatus("error");
      } finally {
        hasLoadedOnce.current = true;
      }
    }

    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <div>
      <header
        style={{
          borderBottom: "1px solid var(--line)",
          padding: "16px 24px",
          display: "flex",
          alignItems: "baseline",
          gap: 12,
        }}
      >
        <span style={{ fontFamily: "var(--font-display)", fontSize: 22, letterSpacing: 0.3 }}>
          Sanraksha
        </span>
        <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
          Landslide early-warning monitoring — Phase 1 prototype
        </span>
        <StatusIndicator status={status} lastUpdated={lastUpdated} />
      </header>
      <Dashboard readings={readings} status={status} hasLoadedOnce={hasLoadedOnce.current} />
    </div>
  );
}

function StatusIndicator({ status, lastUpdated }) {
  const dotClass =
    status === "ready"
      ? "status-dot status-dot--live"
      : status === "error"
      ? "status-dot status-dot--error"
      : "status-dot";

  const label =
    status === "ready"
      ? lastUpdated
        ? `Updated ${formatRelativeTime(lastUpdated)}`
        : "Live"
      : status === "error"
      ? "Disconnected"
      : "Connecting…";

  return (
    <span className="status-pill">
      <span className={dotClass} />
      {label}
    </span>
  );
}

function formatRelativeTime(date) {
  const seconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  return `${minutes}m ago`;
}
