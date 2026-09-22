import { useEffect, useMemo, useState } from "react";
import { fetchSatelliteLatest, satelliteImageUrl } from "../services/api";

const COLLECTION_LABELS = {
  "sentinel-2-l2a": "Sentinel-2 optical",
  "sentinel-1-grd": "Sentinel-1 SAR",
};

export default function SatelliteObservationPanel({ location }) {
  const [data, setData] = useState(null);
  const [activeCollection, setActiveCollection] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(Date.now());

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!location?.location_id) return;

      setStatus("loading");
      setError("");

      try {
        const result = await fetchSatelliteLatest(location.location_id);
        if (cancelled) return;

        setData(result);
        setActiveCollection(
          result.preferred_collection ||
            result.observations?.[0]?.collection ||
            null
        );
        setStatus("ready");
        setRefreshKey(Date.now());
      } catch (err) {
        if (cancelled) return;
        setStatus("error");
        setError(
          err instanceof Error
            ? err.message
            : "Satellite service is unavailable."
        );
      }
    }

    load();
    const timer = window.setInterval(load, 10 * 60 * 1000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [location?.location_id]);

  const active = useMemo(
    () =>
      data?.observations?.find(
        (item) => item.collection === activeCollection
      ) || null,
    [data, activeCollection]
  );

  function refresh() {
    if (!location?.location_id) return;

    setStatus("loading");
    fetchSatelliteLatest(location.location_id)
      .then((result) => {
        setData(result);
        setActiveCollection(
          result.preferred_collection ||
            result.observations?.[0]?.collection ||
            null
        );
        setRefreshKey(Date.now());
        setStatus("ready");
      })
      .catch((err) => {
        setStatus("error");
        setError(
          err instanceof Error
            ? err.message
            : "Satellite service is unavailable."
        );
      });
  }

  if (!location) return null;

  return (
    <section className="satellite-observation-panel">
      <div className="satellite-observation-header">
        <div>
          <div className="satellite-eyebrow">EARTH OBSERVATION</div>
          <h3>Latest satellite acquisition</h3>
          <p>
            Near-real-time imagery from Copernicus Sentinel data for{" "}
            <strong>{location.location_name}</strong>.
          </p>
        </div>

        <button
          type="button"
          className="satellite-refresh-button"
          onClick={refresh}
          disabled={status === "loading"}
        >
          {status === "loading" ? "Checking…" : "Refresh"}
        </button>
      </div>

      {status === "loading" && !data && (
        <div className="satellite-empty">
          Checking Copernicus for the latest available acquisition…
        </div>
      )}

      {status === "error" && (
        <div className="satellite-error">
          <strong>Satellite feed unavailable.</strong>
          <span>{error}</span>
        </div>
      )}

      {status === "ready" && data && data.observations?.length === 0 && (
        <div className="satellite-empty">
          No Sentinel acquisition was found in the configured lookback window.
        </div>
      )}

      {data?.observations?.length > 0 && (
        <>
          <div className="satellite-source-tabs" role="tablist">
            {data.observations.map((observation) => {
              const activeTab = observation.collection === activeCollection;
              return (
                <button
                  key={observation.collection}
                  type="button"
                  role="tab"
                  aria-selected={activeTab}
                  className={`satellite-source-tab${activeTab ? " is-active" : ""}`}
                  onClick={() => setActiveCollection(observation.collection)}
                >
                  {COLLECTION_LABELS[observation.collection] ||
                    observation.mission}
                </button>
              );
            })}
          </div>

          {active && (
            <div className="satellite-observation-content">
              <div className={"satellite-image-frame" + cloudClass(active.cloud_cover_pct)}>
                <img
                  src={satelliteImageUrl(
                    location.location_id,
                    active,
                    refreshKey
                  )}
                  alt={`${active.mission} satellite view of ${location.location_name}`}
                  loading="lazy"
                />
                <div className="satellite-image-badge">
                  <span>{active.mission}</span>
                  <span>LATEST SCENE</span>
                </div>
              </div>

              <div className="satellite-metadata">
                {active.cloud_cover_pct !== null &&
                  active.cloud_cover_pct !== undefined && (
                    <div className={"satellite-cloud-status " + cloudStatus(active.cloud_cover_pct).className}>
                      <span>Image quality</span>
                      <strong>{cloudStatus(active.cloud_cover_pct).label}</strong>
                      <small>
                        {Number(active.cloud_cover_pct).toFixed(1)}% cloud cover
                      </small>
                    </div>
                  )}

                <div>
                  <span>Acquisition</span>
                  <strong>{formatDate(active.acquired_at)}</strong>
                </div>

                <div>
                  <span>Scene</span>
                  <strong title={active.scene_id}>
                    {shortSceneId(active.scene_id)}
                  </strong>
                </div>

                {active.cloud_cover_pct !== null &&
                  active.cloud_cover_pct !== undefined && (
                    <div>
                      <span>Cloud cover</span>
                      <strong>
                        {Number(active.cloud_cover_pct).toFixed(1)}%
                      </strong>
                    </div>
                  )}

                {active.timeliness && (
                  <div>
                    <span>Processing</span>
                    <strong>{active.timeliness}</strong>
                  </div>
                )}

                {active.orbit_direction && (
                  <div>
                    <span>Orbit</span>
                    <strong>{active.orbit_direction}</strong>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="satellite-source-note">
            Source: Copernicus Data Space Ecosystem · Sentinel Hub. Satellite
            acquisitions are discrete observations, not a continuous video
            stream.
          </div>
        </>
      )}
    </section>
  );
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function shortSceneId(value) {
  if (!value) return "—";
  return value.length > 32
    ? `${value.slice(0, 16)}…${value.slice(-12)}`
    : value;
}

function cloudStatus(value) {
  const cloud = Number(value);

  if (!Number.isFinite(cloud)) {
    return { label: "UNKNOWN", className: "is-unknown" };
  }

  if (cloud <= 20) {
    return { label: "CLEAR", className: "is-clear" };
  }

  if (cloud <= 50) {
    return { label: "PARTIAL CLOUD", className: "is-partial" };
  }

  return { label: "CLOUDY", className: "is-cloudy" };
}

function cloudClass(value) {
  const cloud = Number(value);

  if (!Number.isFinite(cloud)) return "";
  if (cloud > 50) return " is-cloudy";
  if (cloud > 20) return " is-partial";
  return " is-clear";
}
