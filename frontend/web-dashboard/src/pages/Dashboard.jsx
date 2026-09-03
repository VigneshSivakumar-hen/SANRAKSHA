import { useEffect, useState } from "react";
import { fetchDashboard, submitReading } from "../services/api";
import RiskCard from "../components/RiskCard";
import RiskMap from "../components/RiskMap";

const RISK_COLOR = {
  LOW: "var(--risk-low)",
  MODERATE: "var(--risk-moderate)",
  HIGH: "var(--risk-high)",
  CRITICAL: "var(--risk-critical)",
};

const EMPTY_FORM = { rainfall_mm_24h: "", soil_moisture_pct: "", slope_deg: "" };

export default function Dashboard() {
  const [readings, setReadings] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  const [form, setForm] = useState(EMPTY_FORM);
  const [manualResult, setManualResult] = useState(null);
  const [manualStatus, setManualStatus] = useState("idle"); // idle | loading | error

  useEffect(() => {
    fetchDashboard()
      .then((data) => {
        setReadings(data);
        setSelectedId(data[0]?.location_id ?? null);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

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

  if (status === "loading") {
    return <Centered>Loading monitoring data…</Centered>;
  }

  if (status === "error") {
    return (
      <Centered>
        Couldn't reach the backend at /api. Make sure the FastAPI server is running on port 8000.
      </Centered>
    );
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, padding: 24 }}>
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

      {/* Main area: map, detail panel, manual test tool */}
      <div>
        <RiskMap readings={readings} selectedId={selectedId} onSelect={setSelectedId} />

        {selected && (
          <div
            style={{
              marginTop: 20,
              background: "var(--panel)",
              border: "1px solid var(--line)",
              borderLeft: `3px solid ${RISK_COLOR[selected.risk_level]}`,
              borderRadius: 4,
              padding: "18px 20px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <h3 style={{ fontFamily: "var(--font-display)", fontSize: 22, margin: 0 }}>
                {selected.location_name}, {selected.state}
              </h3>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 14,
                  color: RISK_COLOR[selected.risk_level],
                }}
              >
                {selected.risk_level} · {selected.risk_score.toFixed(0)}
              </span>
            </div>

            <dl style={dlGrid}>
              <Metric label="Rainfall (24h)" value={`${selected.rainfall_mm_24h} mm`} />
              <Metric label="Soil moisture" value={`${selected.soil_moisture_pct}%`} />
              <Metric label="Slope" value={`${selected.slope_deg}°`} />
            </dl>

            <p style={{ color: "var(--text-muted)", fontSize: 13, margin: "14px 0 4px" }}>
              Contributing factors
            </p>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
              {selected.contributing_factors.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>

            <p style={{ marginTop: 14, fontSize: 14 }}>
              <strong style={{ color: RISK_COLOR[selected.risk_level] }}>Recommendation: </strong>
              {selected.recommendation}
            </p>
          </div>
        )}

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
              Couldn't run the assessment. Check that all three fields are filled in.
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

function Metric({ label, value }) {
  return (
    <div style={{ marginTop: 10 }}>
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
        height: "100vh",
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
  margin: "16px 0 0",
};
