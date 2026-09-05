const path_ = require('path');
const topojson = require('topojson-client');
const d3geo = require('d3-geo');
const fs = require('fs');

const topo = require(path_.join(__dirname, 'india-states-simplified.topo.json'));
const fc = topojson.feature(topo, topo.objects.india_states);

const W = 760, H = 860;
const projection = d3geo.geoMercator().fitSize([W, H], fc);
const path = d3geo.geoPath(projection);

const states = fc.features
  .map((f) => ({ name: f.properties.NAME_1, d: path(f) }))
  .filter((s) => s.d);

// Same 5 demo locations as backend/data/sample/sample_readings.json.
// If you add/change monitored locations, update this list and re-run
// this script (see tools/build-india-map.js) to regenerate projected
// pixel coordinates.
const locations = [
  { id: 'munnar-01', lat: 10.0889, lon: 77.0595 },
  { id: 'wayanad-02', lat: 11.6854, lon: 76.132 },
  { id: 'nilgiris-03', lat: 11.4064, lon: 76.6932 },
  { id: 'darjeeling-04', lat: 27.041, lon: 88.2663 },
  { id: 'shimla-05', lat: 31.1048, lon: 77.1734 },
];

const projected = {};
for (const loc of locations) {
  const [x, y] = projection([loc.lon, loc.lat]);
  projected[loc.id] = [Math.round(x * 100) / 100, Math.round(y * 100) / 100];
}

fs.writeFileSync(
  path_.join(__dirname, '../frontend/web-dashboard/src/data/indiaMapData.js'),
  `// AUTO-GENERATED at build time from a simplified India state boundary
// dataset (mapshaper, 0.5% simplification of GADM-derived polygons) via
// d3-geo's Mercator projection fitted to a ${W}x${H} viewBox.
//
// Do not hand-edit. If monitored locations change, update the location
// list in tools/build-india-map.js and re-run it to regenerate
// PROJECTED_LOCATIONS. State outlines (INDIA_STATE_PATHS) only need
// regenerating if the viewBox size changes.
export const MAP_WIDTH = ${W};
export const MAP_HEIGHT = ${H};
export const INDIA_STATE_PATHS = ${JSON.stringify(states)};
export const PROJECTED_LOCATIONS = ${JSON.stringify(projected, null, 2)};
`
);

console.log('states:', states.length);
console.log('projected:', projected);
