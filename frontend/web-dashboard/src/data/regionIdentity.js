import { Leaf, TreePine, Mountain, CloudFog, MountainSnow, MapPin } from "lucide-react";

// Gives each monitored region its own icon + short terrain description,
// independent of risk level (risk color stays the one saturated signal —
// see RiskCard/RISK_COLOR). If a location_id shows up that isn't listed
// here (e.g. a new region added on the backend), DEFAULT_IDENTITY is used
// so nothing breaks — but it's worth adding a real entry for it.
const REGION_IDENTITY = {
  "munnar-01": { icon: Leaf, terrain: "Tea-garden hills" },
  "wayanad-02": { icon: TreePine, terrain: "Dense forest slope" },
  "nilgiris-03": { icon: Mountain, terrain: "Blue Mountains range" },
  "darjeeling-04": { icon: CloudFog, terrain: "Steep tea escarpment" },
  "shimla-05": { icon: MountainSnow, terrain: "Himalayan ridge" },
};

const DEFAULT_IDENTITY = { icon: MapPin, terrain: "Monitored slope" };

export function getRegionIdentity(locationId) {
  return REGION_IDENTITY[locationId] ?? DEFAULT_IDENTITY;
}
