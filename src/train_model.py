"""
CINEIQ - Model Training Script
==============================
Trains SVD collaborative filtering model using Surprise library.
Logs hyperparameters, RMSE, and ranking metrics (Precision@K, Recall@K,
NDCG@K) to MLflow, and writes metrics.json for DVC to track.

Reads its hyperparameters from params.yaml so runs are reproducible via
`dvc repro` and comparable across experiments in MLflow.
"""

import json
import math
import os
import pickle
from collections import defaultdict
from pathlib import Path

import mlflow
import pandas as pd
import yaml
from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import train_test_split

print("=" * 60)
print("CINEIQ Model Training")
print("=" * 60)

# ============= PATHS =============
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RATINGS_FILE = DATA_DIR / "movielens" / "ratings.csv"
MODEL_FILE = BASE_DIR / "models" / "svd_model.pkl"
PARAMS_FILE = BASE_DIR / "params.yaml"
METRICS_FILE = BASE_DIR / "metrics.json"

MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)

# ============= LOAD PARAMS =============
with open(PARAMS_FILE) as f:
    params = yaml.safe_load(f)

train_params = params["train"]
eval_params = params["eval"]
K = eval_params["k"]
REL_THRESHOLD = eval_params["relevance_threshold"]

# ============= MLflow SETUP =============
# Falls back to a local ./mlruns folder if no tracking server is configured,
# so this script still runs before DagsHub credentials are wired up.
mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file:{BASE_DIR / 'mlruns'}"))
mlflow.set_experiment("cineiq-svd")


def ranking_metrics(predictions, k: int, threshold: float):
    """
    Compute Precision@K, Recall@K and NDCG@K from Surprise test predictions.
    Only users with at least one relevant item in the test split are counted,
    matching standard offline recsys evaluation practice.
    """
    by_user = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        by_user[uid].append((iid, true_r, est))

    precisions, recalls, ndcgs = [], [], []

    for uid, items in by_user.items():
        items.sort(key=lambda x: x[2], reverse=True)  # rank by predicted score
        top_k = items[:k]

        n_relevant = sum(1 for (_, true_r, _) in items if true_r >= threshold)
        if n_relevant == 0:
            continue  # nothing relevant to rank against for this user

        n_relevant_in_top_k = sum(1 for (_, true_r, _) in top_k if true_r >= threshold)

        precisions.append(n_relevant_in_top_k / k)
        recalls.append(n_relevant_in_top_k / n_relevant)

        dcg = sum(
            (1.0 / math.log2(i + 2)) for i, (_, true_r, _) in enumerate(top_k) if true_r >= threshold
        )
        idcg = sum(1.0 / math.log2(i + 2) for i in range(min(n_relevant, k)))
        ndcgs.append(dcg / idcg if idcg > 0 else 0.0)

    n_users = len(precisions)
    return {
        "precision_at_k": sum(precisions) / n_users if n_users else 0.0,
        "recall_at_k": sum(recalls) / n_users if n_users else 0.0,
        "ndcg_at_k": sum(ndcgs) / n_users if n_users else 0.0,
        "n_users_evaluated": n_users,
    }

mlflow.set_experiment("cineiq-svd")

with mlflow.start_run() as run:
    mlflow.log_params({f"train.{k}": v for k, v in train_params.items()})
    mlflow.log_params({f"eval.{k}": v for k, v in eval_params.items()})

    print("\n[1/5] Loading ratings data...")
    ratings = pd.read_csv(RATINGS_FILE)
    print(f"   Loaded {len(ratings):,} ratings from {ratings['userId'].nunique():,} users")
    mlflow.log_param("n_ratings", len(ratings))
    mlflow.log_param("n_users", ratings["userId"].nunique())

    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings[["userId", "movieId", "rating"]], reader)

    trainset, testset = train_test_split(
        data,
        test_size=train_params["test_size"],
        random_state=train_params["random_state"],
    )

    print("\n[2/5] Training SVD model...")
    model = SVD(
        n_factors=train_params["n_factors"],
        n_epochs=train_params["n_epochs"],
        lr_all=train_params["lr_all"],
        reg_all=train_params["reg_all"],
        random_state=train_params["random_state"],
    )
    model.fit(trainset)

    print("\n[3/5] Evaluating model (RMSE)...")
    predictions = model.test(testset)
    rmse = accuracy.rmse(predictions)

    print(f"\n[4/5] Evaluating ranking quality (Precision/Recall/NDCG@{K})...")
    rank_metrics = ranking_metrics(predictions, k=K, threshold=REL_THRESHOLD)
    print(f"   Precision@{K}: {rank_metrics['precision_at_k']:.4f}")
    print(f"   Recall@{K}:    {rank_metrics['recall_at_k']:.4f}")
    print(f"   NDCG@{K}:      {rank_metrics['ndcg_at_k']:.4f}")

    all_metrics = {"rmse": rmse, **rank_metrics}
    mlflow.log_metrics({k: v for k, v in all_metrics.items() if isinstance(v, (int, float))})

    print("\n[5/5] Saving model + metrics...")
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)
    mlflow.log_artifact(str(MODEL_FILE))

    with open(METRICS_FILE, "w") as f:
        json.dump(all_metrics, f, indent=2)

    # Register the model version in the MLflow Model Registry, if the
    # tracking server supports it (DagsHub does; a local file store does not).
    try:
        model_uri = f"runs:/{run.info.run_id}/svd_model.pkl"
        mlflow.register_model(model_uri, "cineiq-svd")
    except Exception as e:
        print(f"   (Model registry not available, skipping registration: {e})")

    print(f"\n✅ Model saved to: {MODEL_FILE}")
    print(f"✅ Metrics saved to: {METRICS_FILE}")
    print(f"✅ MLflow run: {run.info.run_id}")
    print("=" * 60)
