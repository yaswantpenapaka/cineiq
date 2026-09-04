# CineIQ — MLOps Architecture

This document explains the MLOps layer added on top of the CineIQ recommender:
data/model versioning, experiment tracking, and gated model promotion.

## The three pieces

### 1. Data & model versioning — DVC + DagsHub

`data/movielens/ratings.csv` and `models/svd_model.pkl` are tracked with DVC
instead of raw Git. Git only stores small `.dvc` pointer files (a hash and a
path); the actual multi-hundred-MB files live in a DagsHub remote. This means:

- Every commit can be traced back to the *exact* data and model version that
  produced it — `git log` on a `.dvc` file is a full artifact history.
- `dvc pull` in CI reproduces the same environment a teammate (or CI runner)
  needs, without committing huge binaries to Git.

### 2. Reproducible training — `dvc.yaml` + `params.yaml`

Hyperparameters (`n_factors`, `n_epochs`, `lr_all`, `reg_all`, ...) live in
`params.yaml`, not hardcoded in `train_model.py`. `dvc.yaml` declares the
training stage's dependencies, parameters, and outputs. Running:

```bash
dvc repro
```

only re-executes `train_model.py` if `ratings.csv`, the training code, or a
value in `params.yaml` actually changed — otherwise it reuses the cached
`models/svd_model.pkl`. This is the difference between "a script that trains
a model" and "a reproducible pipeline."

### 3. Experiment tracking & model registry — MLflow (hosted on DagsHub)

Every run of `train_model.py` logs to MLflow:

- **Params**: all of `params.yaml`, plus dataset size (`n_ratings`, `n_users`)
- **Metrics**: RMSE, and ranking quality — Precision@10, Recall@10, NDCG@10,
  computed from the held-out test split (standard offline recsys evaluation)
- **Artifact**: the trained `svd_model.pkl`
- **Registry entry**: a new version registered under the `cineiq-svd` model

This makes every training run comparable side-by-side in the MLflow UI,
instead of overwriting `svd_model.pkl` blind and hoping it's better.

### 4. Gated promotion — `scripts/eval_gate.py`

A new model version is only promoted to the `champion` alias in the MLflow
Model Registry if it matches or beats the *current* champion on every
tracked metric (lower RMSE, higher Precision/Recall/NDCG). This runs
automatically in CI after every `dvc repro` — so a regression never gets
silently deployed just because someone pushed a retrain.

## CI pipeline (`.github/workflows/ci.yml`)

On every push/PR to `main`:

1. Install dependencies
2. `dvc pull` — fetch the current data + model from DagsHub
3. `pytest tests/ -v` — unit tests
4. `dvc repro` — retrain only if inputs changed
5. `scripts/eval_gate.py` — promote the new model only if it's actually better
6. `dvc push` — publish updated artifacts back to the DVC remote

## Talking points for interviews

- "I separated training config from code using `params.yaml`, so hyperparameter
  sweeps don't require code changes."
- "Data and model artifacts are versioned with DVC — Git stays lightweight,
  but every commit is traceable to an exact model + dataset snapshot."
- "Every training run is logged to MLflow with both accuracy (RMSE) and
  ranking-quality metrics (Precision/Recall/NDCG@K), not just loss."
- "Model promotion is automated and gated in CI — a retrain only replaces
  the production model if it's measurably at least as good."
