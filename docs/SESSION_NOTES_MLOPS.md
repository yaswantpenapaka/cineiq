# CineIQ MLOps Integration — Session Notes

**Repo:** https://github.com/yaswantpenapaka/cineiq
**Goal:** Add resume/interview-worthy MLOps to CineIQ — data/model versioning, experiment tracking, and gated model promotion — without over-engineering a BTech project.

---

## 1. How we got here

- Started from a Docker RAM crash: both `api` and `streamlit` containers loaded the SVD model + full CSVs independently (confirmed in `src/hybrid_recommender.py`, imported by both `api/main.py` and `app/app.py`), roughly doubling memory use inside a 7.6 GB Docker Desktop limit. **This fix is still pending** — see "Not done yet" below.
- Pivoted to the actual ask: build a real MLOps story for the resume. Agreed scope, in priority order:
  1. **DVC** — version the large data/model files
  2. **MLflow** — track training runs (params + metrics)
  3. **CI eval-gate** — GitHub Actions only promotes a model if it's measurably better
- Chose **DagsHub** (free) as the single backend for both the DVC remote and the MLflow tracking server, to avoid juggling separate Google Drive OAuth + a self-hosted MLflow server.

---

## 2. What's been built (files, all already pushed... *pending final push — see status below*)

| File | Purpose |
|---|---|
| `params.yaml` | SVD hyperparameters + eval config (`k`, `relevance_threshold`), pulled out of code |
| `dvc.yaml` | Pipeline stage: `ratings.csv` + `params.yaml` + `train_model.py` → `svd_model.pkl` + `metrics.json` |
| `dvc.lock` | Auto-generated hash lockfile — makes `dvc repro` skip retraining if nothing changed |
| `src/train_model.py` | Rewritten: reads `params.yaml`, logs params/metrics/artifact to MLflow, computes **Precision@10 / Recall@10 / NDCG@10** (not just RMSE) from the held-out test split, writes `metrics.json`, registers model version in MLflow Model Registry |
| `scripts/eval_gate.py` | Compares latest run's metrics against whatever holds the `champion` alias in the MLflow registry; only promotes if it matches/beats it on every metric |
| `.github/workflows/ci.yml` | On push/PR to `main`: install deps → `dvc pull` → `pytest` → `dvc repro` → `eval_gate.py` → `dvc push` |
| `.gitignore` | Rewritten — **critical fix**: the original blanket `data/`, `models/`, `*.csv`, `*.pkl` rules would have hidden DVC's own pointer files from Git. Replaced with precise ignores (raw untracked MovieLens/TMDB/IMDB files, `feedback/*.csv`, `mlruns/`) that don't shadow `data/movielens/`, `data/`, or `models/` themselves |
| `MLOPS.md` | One-page architecture doc + interview talking points |

### Local verification (already done, working)
```
dvc init -f
dvc remote add origin https://dagshub.com/yaswantpenapaka/cineiq.dvc
dvc remote modify origin --local auth basic
dvc remote modify origin --local user yaswantpenapaka
dvc remote modify origin --local password <token>
dvc remote default origin

dvc add data/movielens/ratings.csv
dvc add data/merged_movies.csv
dvc repro          # trained model, RMSE 0.7745, Precision@10 0.6178, Recall@10 0.7134, NDCG@10 0.8647
python scripts/eval_gate.py   # first run: no champion yet, promotes unconditionally
```

`git status` is clean and fully staged as of the last message — commit was about to be run.

---

## 3. Current status / what to do next

You were mid-way through the final push when this session ended. Pick up exactly here:

```bash
git commit -m "Add MLOps: DVC pipeline + MLflow tracking + eval gating"
git push
dvc push
```

`dvc push` will take a while (uploading ~678 MB `ratings.csv`, `merged_movies.csv`, and ~750 MB `svd_model.pkl` to DagsHub for the first time).

### After that push succeeds:
1. **Add GitHub Actions secrets** (if not done yet): repo Settings → Secrets and variables → Actions → add `DAGSHUB_USERNAME` and `DAGSHUB_TOKEN`.
2. **Push to `main` and check the Actions tab** — confirm the full pipeline goes green: `dvc pull` → `pytest` → `dvc repro` (should skip, nothing changed) → `eval_gate.py` → `dvc push`.
3. **Verify DagsHub UI** — Experiments tab should show the MLflow run; Data tab should show the DVC-tracked files.

### Not done yet (from the original Docker RAM issue, before we pivoted to MLOps)
- Streamlit (`app/app.py`) still imports `src.hybrid_recommender` directly, which independently loads the model + data — duplicating what the API container already loads. Fix: make Streamlit call the FastAPI backend over HTTP instead of loading the model itself. This solves both the RAM crash and is the architecturally-correct pattern. **Not started.**

### Optional next MLOps steps (discussed, not built)
- Wire MLflow into `precompute_sentiment.py` / `prepare_data.py` as a second tracked experiment, if you want the story to cover the full pipeline, not just training.
- Add a scheduled retrain (cron / GitHub Actions `schedule` trigger) so `dvc repro` runs periodically, not just on push.

---

## 4. Where we struggled (so you don't have to re-debug these)

1. **`dvc init` failed**: `ImportError: cannot import name '_DIR_MARK' from 'pathspec.patterns.gitwildmatch'`.
   → Root cause: `pathspec>=0.12.0` removed an internal symbol that DVC 3.55.2 still imports.
   → Fix: `pip install "pathspec==0.11.2" --force-reinstall`

2. **`dvc init` second error**: `'.dvc' exists. Use -f to force.` — leftover from the failed first attempt.
   → Fix: `dvc init -f` (safe, nothing had been tracked yet).

3. **`dvc add ... models/svd_model.pkl` failed**: `overlaps with an output of stage: 'train' in dvc.yaml`.
   → Root cause: the model is a **pipeline output** (declared in `dvc.yaml`), so it can't *also* be manually `dvc add`-ed — those are two different tracking mechanisms. `dvc repro` tracks it automatically via `dvc.lock`. Only `ratings.csv` and `merged_movies.csv` (plain inputs, not pipeline outputs) need explicit `dvc add`.

4. **Original `.gitignore` would have silently broken everything**: it blanket-ignored `data/`, `models/`, `*.csv`, `*.pkl` — which would also hide the small `.dvc` pointer files DVC needs committed (Git doesn't recurse into ignored directories, so even negation patterns can't rescue files inside them). Caught this *before* it caused a silent failure by inspecting the file directly. Rewrote it to ignore only the specific untracked raw files by name.

5. **Terminal echo confusion**: after a `dvc repro` run, the terminal appeared to try to "execute" the previous command's output as new commands (`'CINEIQ' is not recognized...` etc.). This was just a display/paste artifact, not a real error — the actual `dvc repro` output above it had completed successfully.

6. **Stray root-level files**: a leftover `svd_model.pkl` (748 MB, old, sitting in the repo root instead of `models/`) and an empty `python` file (likely an accidental shell redirect) appeared as untracked once the blanket `.gitignore` was narrowed. Deleted both — they weren't part of the real pipeline output (`models/svd_model.pkl`, dated correctly, was safe).

7. **`dvc push` failed**: `no remote specified` — the remote (`origin`) had been added but never set as default.
   → Fix: `dvc remote default origin`, then `dvc push`.

8. **Confusion point worth flagging for future you**: `merged_movies.csv` needed its *own* separate `dvc add` — it wasn't automatically covered by tracking `ratings.csv`. Any new data file you want versioned needs an explicit `dvc add <file>` (or to be declared as a `dvc.yaml` stage output).

---

## 5. Key numbers to remember for interviews

- **RMSE:** 0.7745
- **Precision@10:** 0.6178
- **Recall@10:** 0.7134
- **NDCG@10:** 0.8647
- **Caveat to state honestly if asked:** these ranking metrics are computed against each user's *held-out test-set items* (the 20% split), not the full ~62K-movie catalog — standard offline recsys evaluation, but a smaller/easier ranking task than full-catalog retrieval. Say this if asked; don't oversell it as full-catalog ranking.
