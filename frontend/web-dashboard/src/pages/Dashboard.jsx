import { useEffect, useState } from "react";
import { submitReading } from "../services/api";
import { getRegionIdentity } from "../data/regionIdentity";
import RiskCard from "../components/RiskCard";
import IndiaMap from "../components/IndiaMap";
import MapViewToggle from "../components/MapViewToggle";
import SatelliteMap from "../components/SatelliteMap";
import RiskRings from "../components/RiskRings";
import StateDistribution from "../components/StateDistribution";
import ActivityFeed from "../components/ActivityFeed";
import HistorySparkline from "../components/HistorySparkline";

const RISK_COLOR = {
  LOW: "var(--risk-low)",
  MODERATE: "var(--risk-moderate)",
  HIGH: "var(--risk-high)",
  CRITICAL: "var(--risk-critical)",
};

const EMPTY_FORM = {
  rainfall_mm_24h: "",
  soil_moisture_pct: "",
  slope_deg: "",
};

export default function Dashboard({
  readings = [],
  status,
  hasLoadedOnce,
  refreshKey,
}) { 
  const [selectedId, setSelectedId] = useState(null);
  const [mapView, setMapView] = useState("satellite");
  const [form, setForm] = useState(EMPTY_FORM);
  const [manualResult, setManualResult] = useState(null);
  const [manualStatus, setManualStatus] = useState("idle");

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
   } catch (error) {
     console.error("Manual risk assessment failed:", error);
     setManualStatus("error");
   }

 }

  if (status === "loading" && !hasLoadedOnce) {
    return <Centered>Fetching the latest readings…</Centered>;
  }

  if (status === "error" && readings.length === 0) {
    return (
      <Centered>
        Can't reach the monitoring API right now. It may be waking up from idle — reload in about a minute.
      </Centered>
    );
  }

  return (
    <>
     <style>{`
  /* =========================================================
     SANRAKSHA — FULL WIDTH COMMAND CENTER
     ========================================================= */

  .dashboard-grid.dashboard-shell {
    position: relative;
    left: 50%;
    transform: translateX(-50%);

    width: min(94vw, 1560px);
    max-width: none;

    margin: 0;
    padding: 10px 0 44px;

    display: grid;

    grid-template-columns:
      minmax(240px, 0.82fr)
      minmax(520px, 2.25fr)
      minmax(240px, 0.82fr);

    column-gap: 20px;
    row-gap: 20px;

    align-items: start;
    box-sizing: border-box;
  }

  /* Make sure the three command-center columns
     are allowed to expand */
  .dashboard-shell > * {
    min-width: 0;
    box-sizing: border-box;
  }

  .dashboard-shell .command-feed {
    min-width: 0;
    width: 100%;
  }

  .dashboard-shell .command-tools {
    grid-column: 1 / -1;
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  /* Center map area */
  .dashboard-shell .leaflet-container {
    width: 100%;
  }

  /* =========================================================
     LARGE DESKTOP
     ========================================================= */

  @media (min-width: 1500px) {
    .dashboard-grid.dashboard-shell {
      width: min(94vw, 1560px);

      grid-template-columns:
        minmax(260px, 0.8fr)
        minmax(600px, 2.4fr)
        minmax(260px, 0.8fr);

      column-gap: 24px;
    }
  }

  /* =========================================================
     LAPTOP / TABLET
     ========================================================= */

  @media (max-width: 1180px) {
    .dashboard-grid.dashboard-shell {
      width: min(94vw, 1000px);

      grid-template-columns:
        minmax(220px, 0.85fr)
        minmax(0, 1.8fr);

      column-gap: 16px;
    }

    .dashboard-shell .command-feed {
      grid-column: 1 / -1;
    }

    .dashboard-shell .command-tools {
      grid-column: 1 / -1;
    }
  }

  /* =========================================================
     MOBILE
     ========================================================= */

  @media (max-width: 760px) {
    .dashboard-grid.dashboard-shell {
      position: relative;
      left: 50%;
      transform: translateX(-50%);

      width: 94vw;

      grid-template-columns: 1fr;

      column-gap: 0;
      row-gap: 14px;

      padding-bottom: 28px;
    }

    .dashboard-shell .command-feed,
    .dashboard-shell .command-tools {
      grid-column: auto;
    }
  }
`}</style>
      <div className="dashboard-grid dashboard-shell reveal-once">
        <div>
          <div className="dashboard-section-title">
            <h2 style={{ fontFamily: "var(--font-display)", fontWeight: 500, fontSize: 20, margin: "0 0 12px" }}>
              Monitored locations
            </h2>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-muted)", letterSpacing: "0.08em", whiteSpace: "nowrap", marginBottom: 12 }}>LIVE SITES</span>
          </div>
        {readings.map((r) => (
          <RiskCard key={r.location_id} reading={r} selected={r.location_id === selectedId} onSelect={setSelectedId} />
        ))}
        <StateDistribution readings={readings} />
      </div>

      <div>
        <div style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 6, padding: "16px 20px", marginBottom: 16 }}>
          <RiskRings readings={readings} />
        </div>

        <MapViewToggle value={mapView} onChange={setMapView} />

        {mapView === "satellite" ? (
          <SatelliteMap readings={readings} selectedId={selectedId} onSelect={setSelectedId} />
        ) : (
          <IndiaMap readings={readings} selectedId={selectedId} onSelect={setSelectedId} />
        )}

        {selected && <DetailPanel reading={selected} />}
      </div>

      <div className="command-feed">
        <ActivityFeed readings={readings} refreshKey={refreshKey} onSelect={setSelectedId} />
      </div>

      <div className="command-tools" style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 6, padding: "18px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center", marginBottom: 14 }}>
          <div>
            <h3 style={{ fontFamily: "var(--font-display)", fontSize: 18, margin: 0 }}>Test a manual reading</h3>
            <p style={{ margin: "4px 0 0", color: "var(--text-muted)", fontSize: 12 }}>
              Run the prediction endpoint with custom environmental data.
            </p>
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-muted)", border: "1px solid var(--line)", borderRadius: 999, padding: "5px 9px" }}>
            AI PREDICTION
          </span>
        </div>

        <form onSubmit={handleManualSubmit} style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "end" }}>
          <Field label="Rainfall 24h (mm)" value={form.rainfall_mm_24h} onChange={(v) => setForm({ ...form, rainfall_mm_24h: v })} />
          <Field label="Soil moisture (%)" value={form.soil_moisture_pct} onChange={(v) => setForm({ ...form, soil_moisture_pct: v })} />
          <Field label="Slope (°)" value={form.slope_deg} onChange={(v) => setForm({ ...form, slope_deg: v })} />
          <button type="submit" disabled={manualStatus === "loading"} style={{ background: "var(--panel-raised)", border: "1px solid var(--line)", borderRadius: 4, color: "var(--text)", padding: "8px 16px", cursor: manualStatus === "loading" ? "wait" : "pointer", height: 38, fontFamily: "var(--font-mono)", fontSize: 12 }}>
            {manualStatus === "loading" ? "Assessing…" : "Assess risk"}
          </button>
        </form>

        {manualStatus === "error" && <p style={{ color: "var(--risk-high)", fontSize: 13, marginTop: 10 }}>Couldn't run that assessment — fill in all three fields and try again.</p>}

        {manualResult && (
          <div style={{ marginTop: 16, padding: "12px 14px", border: "1px solid var(--line)", borderLeft: `3px solid ${RISK_COLOR[manualResult.risk_level] ?? "var(--text-muted)"}`, borderRadius: 5, background: "var(--panel-raised)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
              <span style={{ fontFamily: "var(--font-mono)", color: RISK_COLOR[manualResult.risk_level] ?? "var(--text-muted)" }}>
                {manualResult.risk_level} · {Number(manualResult.risk_score).toFixed(0)}
              </span>
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Prediction result</span>
            </div>
            <p style={{ margin: "8px 0 0", fontSize: 13 }}>{manualResult.recommendation}</p>
          </div>
        )}
      </div>
      </div>
    </>
  );
}

function DetailPanel({ reading }) {
  const color = RISK_COLOR[reading.risk_level] ?? "var(--text-muted)";
  const { icon: Icon, terrain } = getRegionIdentity(reading.location_id);
  const score = Math.max(0, Math.min(100, Number(reading.risk_score) || 0));
  const factors = Array.isArray(reading.contributing_factors) ? reading.contributing_factors : [];

  return (
    <section style={{ marginTop: 16, background: "var(--panel)", border: "1px solid var(--line)", borderLeft: `3px solid ${color}`, borderRadius: 6, overflow: "hidden" }}>
      <div style={{ padding: "18px 20px", display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-start", minWidth: 0 }}>
          <div style={{ background: "var(--panel-raised)", border: "1px solid var(--line)", borderRadius: 7, padding: 10, flexShrink: 0 }}>
            <Icon size={22} color={color} strokeWidth={1.75} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.12em", marginBottom: 4 }}>SELECTED MONITORING SITE</div>
            <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, lineHeight: 1.1, margin: 0 }}>{reading.location_name}</h3>
            <p style={{ margin: "5px 0 0", color: "var(--text-muted)", fontSize: 12 }}>{reading.state} · {terrain}</p>
          </div>
        </div>
        <div style={{ minWidth: 120, textAlign: "right" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 38, lineHeight: 0.95, color }}>{score.toFixed(0)}</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.08em", color, marginTop: 6 }}>{reading.risk_level}</div>
        </div>
      </div>

      <div style={{ padding: "0 20px 16px" }}>
        <div style={{ height: 5, background: "var(--panel-raised)", borderRadius: 999, overflow: "hidden" }}>
          <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 999, transition: "width 300ms ease" }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 5, color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 9 }}>
          <span>LOW</span><span>MODERATE</span><span>HIGH</span><span>CRITICAL</span>
        </div>
      </div>

      <div style={{ borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", padding: 16, display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>
        <SensorMetric label="Rainfall · 24h" value={`${reading.rainfall_mm_24h} mm`} percent={rainfallPercent(reading.rainfall_mm_24h)} tone={sensorTone("rainfall", reading.rainfall_mm_24h)} />
        <SensorMetric label="Soil moisture" value={`${reading.soil_moisture_pct}%`} percent={clampPercent(reading.soil_moisture_pct)} tone={sensorTone("soil", reading.soil_moisture_pct)} />
        <SensorMetric label="Terrain slope" value={`${reading.slope_deg}°`} percent={slopePercent(reading.slope_deg)} tone={sensorTone("slope", reading.slope_deg)} />
      </div>

      <div style={{ padding: 18, display: "grid", gridTemplateColumns: "minmax(0, 1.05fr) minmax(220px, 0.95fr)", gap: 20 }}>
        <div>
          <PanelLabel>RECENT RISK TREND</PanelLabel>
          <div style={{ minHeight: 88, display: "flex", alignItems: "center", marginTop: 8, padding: "8px 0" }}>
            <HistorySparkline locationId={reading.location_id} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)", fontSize: 10, marginTop: 2 }}>
            <span>Historical readings</span><span>Current: {score.toFixed(0)}</span>
          </div>
        </div>

        <div>
          <PanelLabel>AI ASSESSMENT BASIS</PanelLabel>
          <div style={{ marginTop: 9 }}>
            {factors.length > 0 ? factors.map((factor, index) => (
              <div key={`${factor}-${index}`} style={{ display: "flex", gap: 8, alignItems: "flex-start", marginBottom: 8, fontSize: 12, lineHeight: 1.35 }}>
                <span style={{ width: 5, height: 5, borderRadius: "50%", background: color, marginTop: 5, flexShrink: 0 }} />
                <span>{factor}</span>
              </div>
            )) : <div style={{ color: "var(--text-muted)", fontSize: 12 }}>No contributing factors reported.</div>}
          </div>
        </div>
      </div>

      <div style={{ margin: "0 18px 18px", padding: "13px 15px", background: "var(--panel-raised)", border: "1px solid var(--line)", borderRadius: 5 }}>
        <PanelLabel>RECOMMENDED ACTION</PanelLabel>
        <p style={{ margin: "7px 0 0", fontSize: 13, lineHeight: 1.5 }}><strong style={{ color }}>→ </strong>{reading.recommendation}</p>
      </div>
    </section>
  );
}

function SensorMetric({ label, value, percent, tone }) {
  return (
    <div style={{ background: "var(--panel-raised)", border: "1px solid var(--line)", borderRadius: 5, padding: "12px 13px", minWidth: 0 }}>
      <div style={{ color: "var(--text-muted)", fontSize: 10, marginBottom: 7 }}>{label}</div>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, color: tone, marginBottom: 8 }}>{value}</div>
      <div style={{ height: 3, background: "var(--bg)", borderRadius: 999, overflow: "hidden" }}>
        <div style={{ width: `${percent}%`, height: "100%", background: tone, borderRadius: 999 }} />
      </div>
    </div>
  );
}

function PanelLabel({ children }) {
  return <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em" }}>{children}</div>;
}

function rainfallPercent(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(100, Math.max(0, (n / 150) * 100)) : 0;
}

function slopePercent(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(100, Math.max(0, (n / 45) * 100)) : 0;
}

function clampPercent(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(100, Math.max(0, n)) : 0;
}

function sensorTone(type, value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "var(--text-muted)";
  if (type === "rainfall") {
    if (n >= 100) return "var(--risk-critical)";
    if (n >= 60) return "var(--risk-high)";
    if (n >= 30) return "var(--risk-moderate)";
    return "var(--risk-low)";
  }
  if (type === "soil") {
    if (n >= 85) return "var(--risk-critical)";
    if (n >= 70) return "var(--risk-high)";
    if (n >= 55) return "var(--risk-moderate)";
    return "var(--risk-low)";
  }
  if (type === "slope") {
    if (n >= 35) return "var(--risk-critical)";
    if (n >= 25) return "var(--risk-high)";
    if (n >= 15) return "var(--risk-moderate)";
    return "var(--risk-low)";
  }
  return "var(--text-muted)";
}

function Field({ label, value, onChange }) {
  return (
    <label style={{ fontSize: 12, color: "var(--text-muted)" }}>
      {label}<br />
      <input type="number" required value={value} onChange={(e) => onChange(e.target.value)} style={{ marginTop: 4, background: "var(--bg)", border: "1px solid var(--line)", borderRadius: 4, color: "var(--text)", padding: "8px 10px", width: 140, fontFamily: "var(--font-mono)" }} />
    </label>
  );
}

function Centered({ children }) {
  return <div style={{ height: "calc(100vh - 60px)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)", padding: 24, textAlign: "center" }}>{children}</div>;
}
