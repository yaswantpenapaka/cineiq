# CineIQ local runbook

## Prerequisites

- Miniconda or Anaconda
- Docker Desktop (only for the containerized run)
- At least 6 GB of memory available to Docker: the model is about 750 MB and
  MovieLens ratings are about 678 MB.

## Conda environment

Run these commands from PowerShell in the project root:

```powershell
conda env create -f environment.yml
conda activate cineiq-env
python check_env.py
pytest tests -q
```

To recreate it after dependency changes:

```powershell
conda env remove --name cineiq-env
conda env create -f environment.yml
```

## Run locally

Use two PowerShell windows, both with `cineiq-env` activated:

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

```powershell
streamlit run app/app.py --server.address 127.0.0.1 --server.port 8501
```

- API health check: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`
- UI: `http://127.0.0.1:8501`

## Run the model in Docker

```powershell
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f api
```

Then open the URLs above. Stop the stack with:

```powershell
docker compose down
```

The image contains only the inference application, its trained SVD model,
`merged_movies.csv`, and MovieLens `ratings.csv`. Raw source datasets and local
development files are excluded from the build context.
