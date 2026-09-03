"""
Trains a RandomForest classifier on the landslide dataset and saves it as
a pickle the backend can load at runtime (see app/ml/predictor.py).

Run:
    python ml/training/generate_dataset.py   # once, to create the CSV
    python ml/training/train.py
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "datasets" / "landslide_training_data.csv"
MODEL_OUT = ROOT / "models" / "landslide_model.pkl"
METRICS_OUT = ROOT / "models" / "metrics.json"

FEATURES = ["rainfall_mm_24h", "soil_moisture_pct", "slope_deg", "temperature_c"]
TARGET = "landslide_occurred"


def main():
    if not DATA_PATH.exists():
        raise SystemExit(f"No dataset at {DATA_PATH}. Run generate_dataset.py first.")

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    preds = model.predict(X_test)
    auc = roc_auc_score(y_test, proba)
    report = classification_report(y_test, preds, output_dict=True)

    print(f"ROC-AUC: {auc:.3f}")
    print(classification_report(y_test, preds))

    importances = dict(zip(FEATURES, model.feature_importances_.round(3).tolist()))
    print("Feature importances:", importances)

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, MODEL_OUT)
    print(f"Saved model to {MODEL_OUT}")

    METRICS_OUT.write_text(
        json.dumps({"roc_auc": auc, "feature_importances": importances, "report": report}, indent=2)
    )


if __name__ == "__main__":
    main()
