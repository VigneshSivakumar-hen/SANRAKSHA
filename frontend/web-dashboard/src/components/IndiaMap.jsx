import { INDIA_STATE_PATHS, MAP_WIDTH, MAP_HEIGHT, PROJECTED_LOCATIONS } from "../data/indiaMapData";
import { getRegionIdentity } from "../data/regionIdentity";

const RISK_COLOR = {
  LOW: "var(--risk-low)",
  MODERATE: "var(--risk-moderate)",
  HIGH: "var(--risk-high)",
  CRITICAL: "var(--risk-critical)",
};

// Rough India bounding box, used ONLY as a fallback projection for any
// location that isn't in the precomputed PROJECTED_LOCATIONS table (e.g.
// a new region added on the backend without re-running
// tools/build-india-map.js). It won't align precisely with the real state
// outlines, so those markers get a dashed ring to signal "approximate".
const FALLBACK_BOUNDS = { latMin: 6, latMax: 38, lonMin: 68, lonMax: 98 };

function fallbackProject(lat, lon) {
  const x = ((lon - FALLBACK_BOUNDS.lonMin) / (FALLBACK_BOUNDS.lonMax - FALLBACK_BOUNDS.lonMin)) * MAP_WIDTH;
  const y = MAP_HEIGHT - ((lat - FALLBACK_BOUNDS.latMin) / (FALLBACK_BOUNDS.latMax - FALLBACK_BOUNDS.latMin)) * MAP_HEIGHT;
  return [x, y];
}

// Real geography means some monitored locations sit genuinely close
// together (e.g. Wayanad and Nilgiris, ~60km apart) — their labels would
// overlap at this scale. Rather than hand-placing text, stack labels
// vertically whenever a new one would land within the same rough
// footprint as an already-placed one.
function resolveLabelOffsets(markers) {
  const placed = [];
  return markers.map((m) => {
    let dy = 4;
    let collided = true;
    while (collided) {
      collided = placed.some((p) => Math.abs(p.x - m.x) < 95 && Math.abs(p.y + p.dy - (m.y + dy)) < 13);
      if (collided) dy += 13;
    }
    placed.push({ x: m.x, y: m.y, dy });
    return { ...m, dy };
  });
}

export default function IndiaMap({ readings, selectedId, onSelect }) {
  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--line)",
        borderRadius: 4,
        padding: 12,
      }}
    >
      <svg
        viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
        width="100%"
        height="auto"
        role="img"
        aria-label="Map of India showing monitored landslide-risk locations"
      >
        {INDIA_STATE_PATHS.map((s) => (
          <path key={s.name} d={s.d} fill="var(--panel-raised)" stroke="var(--line)" strokeWidth="0.75" />
        ))}

        {(() => {
          const markers = readings.map((r) => {
            const precomputed = PROJECTED_LOCATIONS[r.location_id];
            const [x, y] = precomputed ?? fallbackProject(r.lat, r.lon);
            return { reading: r, x, y, isApproximate: !precomputed };
          });
          const withOffsets = resolveLabelOffsets(markers);

          return withOffsets.map(({ reading: r, x, y, dy, isApproximate }) => {
            const color = RISK_COLOR[r.risk_level] ?? "var(--text-muted)";
            const isSelected = r.location_id === selectedId;

            return (
              <g key={r.location_id} onClick={() => onSelect(r.location_id)} style={{ cursor: "pointer" }}>
                <g transform={`translate(${x}, ${y})`}>
                  {isSelected && <circle r={13} fill="none" stroke={color} strokeWidth="1" opacity="0.6" />}
                  {isApproximate && (
                    <circle r={10} fill="none" stroke="var(--text-muted)" strokeWidth="1" strokeDasharray="2,2" />
                  )}
                  <circle r={isSelected ? 7 : 5} fill={color} stroke="var(--bg)" strokeWidth="1.5" />
                </g>
                {dy > 4 && (
                  <line x1={x} y1={y} x2={x + 9} y2={y + dy - 4} stroke="var(--line)" strokeWidth="0.75" />
                )}
                <text x={x + 9} y={y + dy} fontFamily="var(--font-mono)" fontSize="11" fill="var(--text-muted)">
                  {r.location_name}
                </text>
              </g>
            );
          });
        })()}
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
