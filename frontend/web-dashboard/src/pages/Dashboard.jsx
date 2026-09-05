import { useEffect, useState } from "react";
import { submitReading } from "../services/api";
import { getRegionIdentity } from "../data/regionIdentity";
import RiskCard from "../components/RiskCard";
import IndiaMap from "../components/IndiaMap";
import SummaryStrip from "../components/SummaryStrip";
import HistorySparkline from "../components/HistorySparkline";

const RISK_COLOR = {
  LOW: "var(--risk-low)",
  MODERATE: "var(--risk-moderate)",
  HIGH: "var(--risk-high)",
  CRITICAL: "var(--risk-critical)",
};

const EMPTY_FORM = { rainfall_mm_24h: "", soil_moisture_pct: "", slope_deg: "" };

export default function Dashboard({ readings, status, hasLoadedOnce }) {
  const [selectedId, setSelectedId] = useState(null);

  const [form, setForm] = useState(EMPTY_FORM);
  const [manualResult, setManualResult] = useState(null);
  const [manualStatus, setManualStatus] = useState("idle"); // idle | loading | error

  // Pick a default selection once data first arrives, without overriding
  // a selection the person already made on a later poll.
  useEffect(() => {
    if (selectedId === null && readings.length > 0) {
      setSelectedId(readings[0].location_id);
    }
  }, [readings, selectedId]);

  const selected = readings.find((r) => r.location_id === selectedId);

  async function handleManualSubmit(e) {
    e.preventDefault();
    setManualStatus("loading");
    try {
      const result = await submitReading({
        rainfall_mm_24h: Number(form.rainfall_mm_24h),
        soil_moisture_pct: Number(form.soil_moisture_pct),
        slope_deg: Number(form.slope_deg),
      });
      setManualResult(result);
      setManualStatus("idle");
    } catch {
      setManualStatus("error");
    }
  }

  if (status === "loading" && !hasLoadedOnce) {
    return <Centered>Fetching the latest readings…</Centered>;
  }

  if (status === "error" && readings.length === 0) {
    return (
      <Centered>
        Can't reach the monitoring API right now. It may be waking up from
        idle — reload in about a minute.
      </Centered>
    );
  }

  return (
    <div className="dashboard-grid reveal-once">
      {/* Left rail: location list */}
      <div>
        <h2 style={{ fontFamily: "var(--font-display)", fontWeight: 500, fontSize: 20, margin: "0 0 12px" }}>
          Monitored locations
        </h2>
        {readings.map((r) => (
          <RiskCard
            key={r.location_id}
            reading={r}
            selected={r.location_id === selectedId}
            onSelect={setSelectedId}
          />
        ))}
      </div>

      {/* Main area: summary, map, detail panel, manual test tool */}
      <div>
        <SummaryStrip readings={readings} />

        <IndiaMap readings={readings} selectedId={selectedId} onSelect={setSelectedId} />

        {selected && <DetailPanel reading={selected} />}

        {/* Manual assessment tool — demonstrates the /api/predict endpoint directly */}
        <div
          style={{
            marginTop: 20,
            background: "var(--panel)",
            border: "1px solid var(--line)",
            borderRadius: 4,
            padding: "18px 20px",
          }}
        >
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 18, margin: "0 0 12px" }}>
            Test a manual reading
          </h3>
          <form onSubmit={handleManualSubmit} style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "end" }}>
            <Field
              label="Rainfall 24h (mm)"
              value={form.rainfall_mm_24h}
              onChange={(v) => setForm({ ...form, rainfall_mm_24h: v })}
            />
            <Field
              label="Soil moisture (%)"
              value={form.soil_moisture_pct}
              onChange={(v) => setForm({ ...form, soil_moisture_pct: v })}
            />
            <Field
              label="Slope (°)"
              value={form.slope_deg}
              onChange={(v) => setForm({ ...form, slope_deg: v })}
            />
            <button
              type="submit"
              disabled={manualStatus === "loading"}
              style={{
                background: "var(--panel-raised)",
                border: "1px solid var(--line)",
                borderRadius: 4,
                color: "var(--text)",
                padding: "8px 16px",
                cursor: "pointer",
                height: 38,
              }}
            >
              {manualStatus === "loading" ? "Assessing…" : "Assess risk"}
            </button>
          </form>

          {manualStatus === "error" && (
            <p style={{ color: "var(--risk-high)", fontSize: 13, marginTop: 10 }}>
              Couldn't run that assessment — fill in all three fields and try again.
            </p>
          )}

          {manualResult && (
            <p style={{ marginTop: 14, fontSize: 14 }}>
              <span style={{ fontFamily: "var(--font-mono)", color: RISK_COLOR[manualResult.risk_level] }}>
                {manualResult.risk_level} · {manualResult.risk_score.toFixed(0)}
              </span>
              {" — "}
              {manualResult.recommendation}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function DetailPanel({ reading }) {
  const color = RISK_COLOR[reading.risk_level] ?? "var(--text-muted)";
  const { icon: Icon, terrain } = getRegionIdentity(reading.location_id);

  return (
    <div
      style={{
        marginTop: 20,
        background: "var(--panel)",
        border: "1px solid var(--line)",
        borderLeft: `3px solid ${color}`,
        borderRadius: 4,
        padding: "20px 22px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
          <div
            style={{
              background: "var(--panel-raised)",
              border: "1px solid var(--line)",
              borderRadius: 6,
              padding: 10,
              flexShrink: 0,
            }}
          >
            <Icon size={22} color={color} strokeWidth={1.75} />
          </div>
          <div>
            <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, margin: 0 }}>
              {reading.location_name}
            </h3>
            <p style={{ margin: "2px 0 0", color: "var(--text-muted)", fontSize: 13 }}>
              {reading.state} · {terrain}
            </p>
          </div>
        </div>

        <div style={{ textAlign: "right" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 32, color, lineHeight: 1 }}>
            {reading.risk_score.toFixed(0)}
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color, marginTop: 4 }}>
            {reading.risk_level}
          </div>
        </div>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 32, marginTop: 20 }}>
        <dl style={dlGrid}>
          <Metric label="Rainfall (24h)" value={`${reading.rainfall_mm_24h} mm`} />
          <Metric label="Soil moisture" value={`${reading.soil_moisture_pct}%`} />
          <Metric label="Slope" value={`${reading.slope_deg}°`} />
        </dl>

        <div>
          <p style={{ color: "var(--text-muted)", fontSize: 11, margin: "0 0 6px" }}>Recent risk trend</p>
          <HistorySparkline locationId={reading.location_id} />
        </div>
      </div>

      <p style={{ color: "var(--text-muted)", fontSize: 13, margin: "18px 0 4px" }}>
        Contributing factors
      </p>
      <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
        {reading.contributing_factors.map((f, i) => (
          <li key={i}>{f}</li>
        ))}
      </ul>

      <p style={{ marginTop: 14, fontSize: 14 }}>
        <strong style={{ color }}>Recommendation: </strong>
        {reading.recommendation}
      </p>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <dt style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "none" }}>{label}</dt>
      <dd style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: 15 }}>{value}</dd>
    </div>
  );
}

function Field({ label, value, onChange }) {
  return (
    <label style={{ fontSize: 12, color: "var(--text-muted)" }}>
      {label}
      <br />
      <input
        type="number"
        required
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          marginTop: 4,
          background: "var(--bg)",
          border: "1px solid var(--line)",
          borderRadius: 4,
          color: "var(--text)",
          padding: "8px 10px",
          width: 140,
          fontFamily: "var(--font-mono)",
        }}
      />
    </label>
  );
}

function Centered({ children }) {
  return (
    <div
      style={{
        height: "calc(100vh - 60px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--text-muted)",
        fontFamily: "var(--font-body)",
        padding: 24,
        textAlign: "center",
      }}
    >
      {children}
    </div>
  );
}

const dlGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(3, auto)",
  gap: 24,
};
