# Sanraksha web dashboard (Phase 1)

React + Vite dashboard that visualizes landslide risk for monitored
locations, backed by the FastAPI service in `../../backend`.

## Run locally

Make sure the backend is running first (`http://localhost:8000`), then:

```bash
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies any request to
`/api/*` through to the backend (see `vite.config.js`), so no CORS setup or
`.env` is needed in development.

## What's here

- `src/pages/Dashboard.jsx` — fetches `/api/dashboard`, renders the location
  list, map, detail panel, and a manual "test a reading" form wired to
  `/api/predict`.
- `src/components/RiskCard.jsx` — one location's risk summary.
- `src/components/RiskMap.jsx` — an abstracted topographic panel (SVG, no
  external map library) plotting each location by risk color.
- `src/services/api.js` — the two fetch calls the app makes.

## Build

```bash
npm run build
```

Outputs a production build to `dist/`.
