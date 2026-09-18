import {
  CircleMarker,
  MapContainer,
  TileLayer,
  Tooltip,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import { getRegionIdentity } from "../data/regionIdentity";


const SATELLITE_TILE_URL =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";


const RISK_COLORS = {
  LOW: "#4ade80",
  MODERATE: "#facc15",
  HIGH: "#fb923c",
  CRITICAL: "#f87171",
};


const INDIA_CENTER = [22.5, 79.0];

const INDIA_BOUNDS = [
  [6, 68],
  [38, 98],
];


export default function SatelliteMap({
  readings = [],
  selectedId = null,
  onSelect,
}) {
  return (
    <div
      className="satellite-map-shell"
      style={{
        position: "relative",
        width: "100%",
        height: 620,
        overflow: "hidden",
        border: "1px solid var(--line)",
        borderRadius: 4,
        background: "#111",
      }}
    >

      <MapContainer
        center={INDIA_CENTER}
        zoom={5}
        minZoom={4}
        maxZoom={12}
        maxBounds={INDIA_BOUNDS}
        maxBoundsViscosity={1}
        scrollWheelZoom={true}
        style={{
          width: "100%",
          height: "100%",
        }}
      >

        {/* =====================================================
            SATELLITE IMAGERY
            ===================================================== */}

        <TileLayer
          url={SATELLITE_TILE_URL}
          attribution="Tiles &copy; Esri &mdash; Esri, Maxar, Earthstar Geographics, and the GIS community"
        />


        {/* =====================================================
            LANDSLIDE RISK LOCATIONS
            ===================================================== */}

        {readings.map((reading) => {

          const latitude = Number(reading.lat);
          const longitude = Number(reading.lon);

          /*
           * Ignore invalid coordinates so one bad API reading
           * cannot crash the entire map.
           */
          if (
            !Number.isFinite(latitude) ||
            !Number.isFinite(longitude)
          ) {
            return null;
          }


          /*
           * Keep only coordinates inside the configured
           * India monitoring bounds.
           */
          if (
            latitude < 6 ||
            latitude > 38 ||
            longitude < 68 ||
            longitude > 98
          ) {
            return null;
          }


          const riskLevel =
            String(reading.risk_level || "LOW").toUpperCase();

          const riskColor =
            RISK_COLORS[riskLevel] || RISK_COLORS.LOW;


          const isSelected =
            reading.location_id === selectedId;


          let terrain = "Terrain information unavailable";

          try {
            const identity = getRegionIdentity(
              reading.location_id
            );

            if (identity?.terrain) {
              terrain = identity.terrain;
            }
          } catch {
            terrain = "Terrain information unavailable";
          }


          return (
            <CircleMarker
              key={reading.location_id}
              center={[latitude, longitude]}
              radius={isSelected ? 11 : 8}
              pathOptions={{
                color: "#ffffff",
                weight: isSelected ? 3 : 2,
                fillColor: riskColor,
                fillOpacity: isSelected ? 1 : 0.85,
              }}
              eventHandlers={{
                click: () => {
                  if (typeof onSelect === "function") {
                    onSelect(reading.location_id);
                  }
                },
              }}
            >

              <Tooltip
                direction="top"
                offset={[0, -8]}
                opacity={1}
              >

                <div
                  style={{
                    minWidth: 180,
                    fontFamily: "Arial, sans-serif",
                  }}
                >

                  <div
                    style={{
                      fontWeight: 700,
                      fontSize: 14,
                      marginBottom: 5,
                    }}
                  >
                    {reading.location_name ||
                      reading.location_id}
                  </div>


                  <div
                    style={{
                      fontSize: 12,
                      marginBottom: 3,
                    }}
                  >
                    {reading.state || "Unknown state"}
                  </div>


                  <div
                    style={{
                      fontSize: 12,
                      marginBottom: 3,
                    }}
                  >
                    Terrain: {terrain}
                  </div>


                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      color: riskColor,
                    }}
                  >
                    Risk: {riskLevel}
                  </div>


                  <div
                    style={{
                      fontSize: 12,
                      marginTop: 3,
                    }}
                  >
                    Score:{" "}
                    {Number(
                      reading.risk_score ?? 0
                    ).toFixed(0)}
                  </div>

                </div>

              </Tooltip>

            </CircleMarker>
          );
        })}

      </MapContainer>


      {/* =====================================================
          MAP LEGEND
          ===================================================== */}

      <div
        style={{
          position: "absolute",
          left: 14,
          bottom: 14,
          zIndex: 1000,
          background: "rgba(15, 23, 42, 0.92)",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: 6,
          padding: "10px 12px",
          color: "#ffffff",
          fontSize: 11,
          backdropFilter: "blur(8px)",
        }}
      >

        <div
          style={{
            fontWeight: 700,
            marginBottom: 7,
            fontSize: 12,
          }}
        >
          Landslide Risk
        </div>


        <LegendItem
          color={RISK_COLORS.LOW}
          label="Low"
        />

        <LegendItem
          color={RISK_COLORS.MODERATE}
          label="Moderate"
        />

        <LegendItem
          color={RISK_COLORS.HIGH}
          label="High"
        />

        <LegendItem
          color={RISK_COLORS.CRITICAL}
          label="Critical"
        />

      </div>


      {/* =====================================================
          LOCATION COUNT
          ===================================================== */}

      <div
        style={{
          position: "absolute",
          right: 14,
          top: 14,
          zIndex: 1000,
          background: "rgba(15, 23, 42, 0.92)",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: 6,
          padding: "8px 11px",
          color: "#ffffff",
          fontSize: 11,
          backdropFilter: "blur(8px)",
        }}
      >
        {readings.length} monitored location
        {readings.length === 1 ? "" : "s"}
      </div>

    </div>
  );
}


/* ================================================================
   LEGEND ITEM
   ================================================================ */

function LegendItem({ color, label }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 7,
        marginTop: 5,
      }}
    >

      <span
        style={{
          width: 9,
          height: 9,
          borderRadius: "50%",
          background: color,
          display: "inline-block",
          boxShadow: "0 0 0 1px rgba(255,255,255,0.5)",
        }}
      />

      <span>{label}</span>

    </div>
  );
}