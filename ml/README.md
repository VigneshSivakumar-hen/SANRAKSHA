# Sanraksha ML training pipeline (Phase 2)

Trains the landslide risk classifier the backend loads at runtime
(`backend/app/ml/predictor.py`).

## Retrain

```bash
pip install -r ../backend/requirements.txt   # scikit-learn, pandas, joblib

python training/generate_dataset.py   # writes datasets/landslide_training_data.csv
python training/train.py              # writes models/landslide_model.pkl + metrics.json
```

The backend picks up `models/landslide_model.pkl` automatically on next
startup (or immediately if you restart it after retraining).

## About the training data

There's no ready-to-use, public, labeled landslide-event dataset bundled
in this repo. `training/generate_dataset.py` generates a synthetic-but-
physically-plausible one instead: rainfall, soil moisture, and slope angle
combine (with a rainfall × soil-moisture interaction term, reflecting the
real-world compound saturation trigger) into a latent risk index, which is
converted into a landslide/no-landslide label via a logistic function plus
noise — producing a dataset with a realistic ~34% positive rate and
genuine, learnable structure, not a hand-coded rule dressed up as ML.

**To train on real data instead:** replace the generated CSV with an
actual labeled dataset in the same columns
(`rainfall_mm_24h, soil_moisture_pct, slope_deg, temperature_c,
landslide_occurred`) — for example India's Geological Survey landslide
inventory joined against IMD rainfall records — and rerun `train.py`
unchanged.

## Current model performance

RandomForestClassifier, 200 trees, max depth 8, class-balanced:

- ROC-AUC: ~0.82 on a held-out 20% test split
- Feature importances roughly: rainfall 36%, soil moisture 30%, slope 26%,
  temperature 8% — consistent with the domain assumptions the synthetic
  data encodes

Full metrics are written to `models/metrics.json` after each training run.
