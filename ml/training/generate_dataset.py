"""
Generates a synthetic landslide training dataset.

There's no public, ready-to-use labeled landslide-event dataset bundled
here, so this script builds one that follows the same physical logic
domain literature uses (rainfall intensity + antecedent soil saturation +
slope angle are the three dominant triggering factors), with realistic
noise and a probabilistic outcome label rather than a hand-drawn rule.

This keeps the trained model honest about what it can currently learn
(the relationships we encoded) while giving you a real training pipeline
to point at actual landslide inventory + rainfall data later — just
replace this script's output with a real labeled CSV in the same columns
and re-run train.py.
"""

import numpy as np
import pandas as pd
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parents[1] / "datasets" / "landslide_training_data.csv"
N_SAMPLES = 6000
SEED = 42


def generate(n=N_SAMPLES, seed=SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    rainfall = rng.gamma(shape=2.0, scale=45, size=n)          # mm, right-skewed
    rainfall = np.clip(rainfall, 0, 400)

    soil_moisture = 20 + 0.25 * rainfall + rng.normal(0, 12, n)  # correlated with rainfall
    soil_moisture = np.clip(soil_moisture, 5, 100)

    slope = rng.uniform(2, 60, n)                                # degrees
    temperature = rng.normal(20, 6, n)

    # Latent risk index combining the three physical drivers, each
    # normalized 0-1, with rainfall x soil_moisture interaction reflecting
    # the compound saturation trigger.
    rainfall_n = np.clip(rainfall / 250, 0, 1)
    soil_n = np.clip(soil_moisture / 100, 0, 1)
    slope_n = np.clip(slope / 55, 0, 1)

    latent = 0.35 * rainfall_n + 0.30 * soil_n + 0.35 * slope_n + 0.25 * (rainfall_n * soil_n)
    latent = latent + rng.normal(0, 0.08, n)  # measurement/model noise

    # Convert latent index to a probability via a logistic squashing
    # centered so the dataset has a realistic, imbalanced positive rate
    # (landslides are rare events even under risky conditions).
    prob = 1 / (1 + np.exp(-8 * (latent - 0.62)))
    occurred = rng.binomial(1, prob)

    df = pd.DataFrame(
        {
            "rainfall_mm_24h": rainfall.round(1),
            "soil_moisture_pct": soil_moisture.round(1),
            "slope_deg": slope.round(1),
            "temperature_c": temperature.round(1),
            "landslide_occurred": occurred,
        }
    )
    return df


if __name__ == "__main__":
    df = generate()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUT_PATH}")
    print(f"Positive rate: {df['landslide_occurred'].mean():.3f}")
