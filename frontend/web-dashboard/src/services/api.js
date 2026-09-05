// In local dev, Vite's dev-server proxy (vite.config.js) forwards "/api" to
// the local backend. In production (a static-site deploy with no proxy),
// set VITE_API_URL to the deployed backend's URL, e.g.
// https://sanraksha-backend.onrender.com — see render.yaml / README.
const rawApiUrl = import.meta.env.VITE_API_URL || "";
// Render's `fromService` env var wiring returns a bare hostname (no
// scheme). If someone pastes a full URL instead, we leave it alone.
const API_ORIGIN =
  rawApiUrl && !rawApiUrl.startsWith("http") ? `https://${rawApiUrl}` : rawApiUrl;
const BASE_URL = `${API_ORIGIN}/api`;

async function handle(res) {
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Request failed (${res.status}): ${body}`);
  }
  return res.json();
}

export async function fetchDashboard() {
  const res = await fetch(`${BASE_URL}/dashboard`);
  return handle(res);
}

export async function submitReading(reading) {
  const res = await fetch(`${BASE_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reading),
  });
  return handle(res);
}

export async function fetchHistory(locationId) {
  const res = await fetch(`${BASE_URL}/locations/${locationId}/history`);
  return handle(res);
}
