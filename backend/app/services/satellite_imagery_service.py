"""
Copernicus Data Space / Sentinel Hub satellite imagery adapter.

This service retrieves the latest available Sentinel-1 GRD and Sentinel-2
L2A observations around a monitored SANRAKSHA location and renders the
selected acquisition through the Sentinel Hub Processing API.

The service is deliberately backend-only: Copernicus OAuth credentials are
read from environment variables and are never sent to the browser.

Sentinel observations are near-real-time / latest-available data, not a
continuous video stream. The satellites have their own revisit and product
availability latency.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

S2_COLLECTION = "sentinel-2-l2a"
S1_COLLECTION = "sentinel-1-grd"
TOKEN_URL = settings.SENTINEL_HUB_TOKEN_URL
BASE_URL = settings.SENTINEL_HUB_BASE_URL.rstrip("/")

_token_lock = threading.Lock()
_token: str | None = None
_token_expires_at = 0.0

_metadata_cache: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}
_image_cache: dict[tuple[str, float, float, str], tuple[float, bytes]] = {}
_cache_lock = threading.Lock()

S2_EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04", "dataMask"],
    output: { bands: 4, sampleType: "AUTO" }
  };
}

function evaluatePixel(sample) {
  var red = Math.min(1, 2.5 * sample.B04);
  var green = Math.min(1, 2.5 * sample.B03);
  var blue = Math.min(1, 2.5 * sample.B02);

  // Make pixels outside valid Sentinel-2 coverage transparent instead of
  // rendering them as black blocks in the dashboard.
  if (sample.dataMask === 0) {
    return [0, 0, 0, 0];
  }

  return [red, green, blue, 1];
}
"""

S1_EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ["VV"],
    output: { bands: 3, sampleType: "AUTO" }
  };
}

function evaluatePixel(sample) {
  var db = 10 * Math.log10(Math.max(sample.VV, 0.000001));
  var value = Math.max(0, Math.min(1, (db + 25) / 25));
  return [value, value, value];
}
"""


def _credentials_configured() -> bool:
    return bool(
        settings.COPERNICUS_CLIENT_ID
        and settings.COPERNICUS_CLIENT_SECRET
    )


def _get_token() -> str:
    global _token, _token_expires_at

    if not _credentials_configured():
        raise RuntimeError(
            "Copernicus credentials are not configured. Set "
            "COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET."
        )

    now = time.time()
    if _token and now < _token_expires_at - 60:
        return _token

    with _token_lock:
        now = time.time()
        if _token and now < _token_expires_at - 60:
            return _token

        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.COPERNICUS_CLIENT_ID,
                "client_secret": settings.COPERNICUS_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()

        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError("Copernicus token response did not contain access_token")

        _token = access_token
        _token_expires_at = now + int(payload.get("expires_in", 3600))
        return _token


def _bbox(lat: float, lon: float) -> list[float]:
    radius = max(0.005, settings.SATELLITE_AOI_RADIUS_DEG)
    return [
        lon - radius,
        lat - radius,
        lon + radius,
        lat + radius,
    ]


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _search_collection(
    lat: float,
    lon: float,
    collection: str,
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(1, settings.SATELLITE_LOOKBACK_DAYS))

    payload: dict[str, Any] = {
        "bbox": _bbox(lat, lon),
        "datetime": f"{start.isoformat().replace('+00:00', 'Z')}/"
        f"{now.isoformat().replace('+00:00', 'Z')}",
        "collections": [collection],
        "limit": 20,
        "fields": {
            "include": [
                "id",
                "properties.datetime",
                "properties.eo:cloud_cover",
                "properties.s1:timeliness",
                "properties.sat:orbit_state",
            ]
        },
    }

    response = requests.post(
        f"{BASE_URL}/catalog/v1/search",
        json=payload,
        headers={
            "Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()

    features = response.json().get("features", [])
    features.sort(
        key=lambda item: _parse_datetime(
            item.get("properties", {}).get("datetime")
        ) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return features


def _normalise_observation(
    collection: str,
    feature: dict[str, Any],
) -> dict[str, Any] | None:
    properties = feature.get("properties") or {}
    acquired_at = properties.get("datetime")
    if not acquired_at:
        return None

    cloud = properties.get("eo:cloud_cover")
    try:
        cloud = float(cloud) if cloud is not None else None
    except (TypeError, ValueError):
        cloud = None

    return {
        "collection": collection,
        "mission": "Sentinel-2" if collection == S2_COLLECTION else "Sentinel-1",
        "scene_id": str(feature.get("id", "unknown")),
        "acquired_at": acquired_at,
        "cloud_cover_pct": cloud,
        "timeliness": properties.get("s1:timeliness"),
        "orbit_direction": properties.get("sat:orbit_state"),
    }


def _latest_for_collection(
    lat: float,
    lon: float,
    collection: str,
) -> dict[str, Any] | None:
    features = _search_collection(lat, lon, collection)
    observations = [
        item
        for item in (
            _normalise_observation(collection, feature)
            for feature in features
        )
        if item is not None
    ]

    if collection == S2_COLLECTION:
        acceptable = [
            item
            for item in observations
            if item["cloud_cover_pct"] is None
            or item["cloud_cover_pct"] <= settings.SATELLITE_MAX_CLOUD_COVER_PCT
        ]
        if acceptable:
            return acceptable[0]

    return observations[0] if observations else None


def get_latest_observations(lat: float, lon: float) -> list[dict[str, Any]]:
    """Return latest available Sentinel-2 and Sentinel-1 observations."""
    if not _credentials_configured():
        raise RuntimeError(
            "Satellite imagery is not configured yet. Add "
            "COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET to the backend."
        )

    cache_key = (round(float(lat), 5), round(float(lon), 5))
    now = time.time()

    with _cache_lock:
        cached = _metadata_cache.get(cache_key)
        if cached and now - cached[0] < settings.SATELLITE_CACHE_SECONDS:
            return cached[1]["observations"]

    observations = []
    errors = []

    for collection in (S2_COLLECTION, S1_COLLECTION):
        try:
            latest = _latest_for_collection(lat, lon, collection)
            if latest:
                observations.append(latest)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{collection}: {exc}")
            logger.warning(
                "Satellite catalog search failed for %s at (%s, %s): %s",
                collection,
                lat,
                lon,
                exc,
            )

    if not observations and errors:
        raise RuntimeError("No Sentinel observations available: " + " | ".join(errors))

    observations.sort(
        key=lambda item: _parse_datetime(item["acquired_at"])
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    with _cache_lock:
        _metadata_cache[cache_key] = (
            now,
            {"observations": observations},
        )

    return observations


def get_latest_for_location(
    lat: float,
    lon: float,
) -> tuple[list[dict[str, Any]], str | None]:
    observations = get_latest_observations(lat, lon)

    if not observations:
        return [], None

    # Prefer Sentinel-2 for the dashboard's visual overview when a usable
    # optical scene exists; Sentinel-1 remains available for cloud-robust SAR.
    preferred = next(
        (
            item["collection"]
            for item in observations
            if item["collection"] == S2_COLLECTION
        ),
        S1_COLLECTION,
    )
    return observations, preferred


def render_observation(
    lat: float,
    lon: float,
    collection: str,
    acquired_at: str,
) -> bytes:
    """Render the selected real Sentinel acquisition as a PNG/JPEG image."""
    if collection not in {S1_COLLECTION, S2_COLLECTION}:
        raise ValueError("Unsupported satellite collection")

    parsed = _parse_datetime(acquired_at)
    if parsed is None:
        raise ValueError("Invalid satellite acquisition timestamp")

    # A narrow time window around the catalog acquisition avoids accidentally
    # returning a different scene while still tolerating tile-level timestamp
    # differences during processing.
    start = parsed - timedelta(minutes=2)
    end = parsed + timedelta(minutes=2)

    cache_key = (
        collection,
        round(float(lat), 5),
        round(float(lon), 5),
        parsed.isoformat(),
    )
    now = time.time()

    with _cache_lock:
        cached = _image_cache.get(cache_key)
        if cached and now - cached[0] < settings.SATELLITE_CACHE_SECONDS:
            return cached[1]

    if collection == S2_COLLECTION:
        evalscript = S2_EVALSCRIPT
        data = {
            "type": S2_COLLECTION,
            "dataFilter": {
                "timeRange": {
                    "from": start.isoformat().replace("+00:00", "Z"),
                    "to": end.isoformat().replace("+00:00", "Z"),
                },
                "mosaickingOrder": "mostRecent",
            },
        }
    else:
        evalscript = S1_EVALSCRIPT
        data = {
            "type": S1_COLLECTION,
            "dataFilter": {
                "timeRange": {
                    "from": start.isoformat().replace("+00:00", "Z"),
                    "to": end.isoformat().replace("+00:00", "Z"),
                },
                "mosaickingOrder": "mostRecent",
            },
            "processing": {
                "orthorectify": "true",
                "demInstance": "COPERNICUS_30",
                "backCoeff": "GAMMA0_TERRAIN",
            },
        }

    payload = {
        "input": {
            "bounds": {
                "bbox": _bbox(lat, lon),
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                },
            },
            "data": [data],
        },
        "output": {
            "width": settings.SATELLITE_IMAGE_WIDTH,
            "height": settings.SATELLITE_IMAGE_HEIGHT,
            "responses": [
                {
                    "identifier": "default",
                    "format": {"type": "image/png" if collection == S2_COLLECTION else "image/jpeg"},
                }
            ],
        },
        "evalscript": evalscript,
    }

    response = requests.post(
        f"{BASE_URL}/process/v1",
        json=payload,
        headers={
            "Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json",
            "Accept": "image/png" if collection == S2_COLLECTION else "image/jpeg",
        },
        timeout=60,
    )
    response.raise_for_status()

    image = response.content
    if not image:
        raise RuntimeError("Sentinel Hub returned an empty satellite image")

    with _cache_lock:
        _image_cache[cache_key] = (now, image)

    return image
