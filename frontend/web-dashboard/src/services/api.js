const BASE_URL = "/api";

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
