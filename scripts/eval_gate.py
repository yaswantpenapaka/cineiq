"""
CINEIQ - Model Promotion Gate
==============================
Compares the metrics of the most recent training run (metrics.json, written
by src/train_model.py) against whichever model version currently holds the
"champion" alias in the MLflow Model Registry. Only promotes the new model
if it's actually as good or better — this is what turns "we retrained a
model" into an automated, gated deployment step, run in CI.

Exit code 0 = passed the gate (promoted, or nothing to compare against yet)
Exit code 1 = new model is worse than the current champion; not promoted
"""

import json
import os
import sys
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient

BASE_DIR = Path(__file__).parent.parent
METRICS_FILE = BASE_DIR / "metrics.json"
MODEL_NAME = "cineiq-svd"
ALIAS = "champion"

# Lower is better for these metrics; everything else, higher is better.
LOWER_IS_BETTER = {"rmse"}


def promote(client: MlflowClient, run_id: str):
    model_uri = f"runs:/{run_id}/svd_model.pkl"
    mv = mlflow.register_model(model_uri, MODEL_NAME)
    client.set_registered_model_alias(MODEL_NAME, ALIAS, mv.version)
    print(f"Promoted version {mv.version} to alias '{ALIAS}'.")


def main():
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file:{BASE_DIR / 'mlruns'}"))
    client = MlflowClient()

    with open(METRICS_FILE) as f:
        new_metrics = json.load(f)

    experiment = client.get_experiment_by_name("cineiq-svd")
    latest_run = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=1,
    )[0]

    try:
        champion_version = client.get_model_version_by_alias(MODEL_NAME, ALIAS)
        champion_metrics = client.get_run(champion_version.run_id).data.metrics
    except Exception:
        print("No existing 'champion' model found — promoting this run unconditionally.")
        promote(client, latest_run.info.run_id)
        return

    print(f"New run metrics:      {new_metrics}")
    print(f"Champion run metrics: {champion_metrics}")

    comparisons = []
    for key, new_val in new_metrics.items():
        if key not in champion_metrics or not isinstance(new_val, (int, float)):
            continue
        old_val = champion_metrics[key]
        comparisons.append(new_val <= old_val if key in LOWER_IS_BETTER else new_val >= old_val)

    if comparisons and all(comparisons):
        print("✅ New model matches or beats the champion on every metric — promoting.")
        promote(client, latest_run.info.run_id)
    else:
        print("❌ New model is worse than the champion on at least one metric — not promoted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
