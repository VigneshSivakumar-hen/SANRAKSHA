const RISK_COLOR = {
  LOW: "var(--risk-low)",
  MODERATE: "var(--risk-moderate)",
  HIGH: "var(--risk-high)",
  CRITICAL: "var(--risk-critical)",
};

// Bounding box loosely covering India's landslide-prone hill regions.
const BOUNDS = { latMin: 8, latMax: 33, lonMin: 74, lonMax: 90 };
const W = 620;
const H = 420;

function project(lat, lon) {
  const x = ((lon - BOUNDS.lonMin) / (BOUNDS.lonMax - BOUNDS.lonMin)) * W;
  const y = H - ((lat - BOUNDS.latMin) / (BOUNDS.latMax - BOUNDS.latMin)) * H;
  return { x, y };
}

// A handful of static contour-line style paths — decorative terrain texture,
// not real elevation data. Kept subtle and used once, as the map's single
// bold visual device.
const CONTOURS = [
  "M20,340 C120,300 220,360 320,320 C420,280 520,330 600,300",
  "M0,260 C100,230 200,270 300,240 C400,210 500,250 620,220",
  "M40,180 C140,150 240,190 340,160 C440,130 520,170 600,150",
  "M10,90 C110,70 210,100 310,80 C410,60 500,90 590,70",
];

export default function RiskMap({ readings, selectedId, onSelect }) {
  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--line)",
        borderRadius: 4,
        padding: 12,
      }}
    >
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="auto" role="img" aria-label="Monitoring locations map">
        {CONTOURS.map((d, i) => (
          <path key={i} d={d} fill="none" stroke="var(--line)" strokeWidth="1" />
        ))}

        {readings.map((r) => {
          const { x, y } = project(r.lat, r.lon);
          const color = RISK_COLOR[r.risk_level] ?? "var(--text-muted)";
          const isSelected = r.location_id === selectedId;
          return (
            <g
              key={r.location_id}
              transform={`translate(${x}, ${y})`}
              onClick={() => onSelect(r.location_id)}
              style={{ cursor: "pointer" }}
            >
              {isSelected && <circle r={12} fill="none" stroke={color} strokeWidth="1" opacity="0.6" />}
              <circle r={isSelected ? 7 : 5} fill={color} stroke="var(--bg)" strokeWidth="1.5" />
              <text
                x={9}
                y={4}
                fontFamily="var(--font-mono)"
                fontSize="11"
                fill="var(--text-muted)"
              >
                {r.location_name}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="map-legend">
        {Object.entries(RISK_COLOR).map(([level, color]) => (
          <span key={level} className="map-legend-item">
            <span className="map-legend-swatch" style={{ background: color }} />
            {level}
          </span>
        ))}
      </div>
    </div>
  );
}
