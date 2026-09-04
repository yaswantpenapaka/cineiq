"""Validate the packages and runtime assets required to serve CineIQ."""

import importlib
import sys
from pathlib import Path

print(f"Python: {sys.version.split()[0]}")

packages = {
    "pandas": "pandas",
    "numpy": "numpy",
    "scikit-learn": "sklearn",
    "scikit-surprise": "surprise",
    "FastAPI": "fastapi",
    "Uvicorn": "uvicorn",
    "Streamlit": "streamlit",
    "VADER Sentiment": "vaderSentiment",
    "LIME": "lime",
}

failures = []
print("\nChecking Python packages:")
for display_name, import_name in packages.items():
    try:
        module = importlib.import_module(import_name)
        print(f"  OK  {display_name} {getattr(module, '__version__', '')}".rstrip())
    except Exception as exc:
        failures.append(display_name)
        print(f"  FAIL {display_name}: {type(exc).__name__}")

project_root = Path(__file__).resolve().parent
assets = [
    project_root / "data" / "merged_movies.csv",
    project_root / "data" / "movielens" / "ratings.csv",
    project_root / "models" / "svd_model.pkl",
]
print("\nChecking runtime assets:")
for asset in assets:
    if asset.is_file() and asset.stat().st_size > 0:
        print(f"  OK  {asset.relative_to(project_root)}")
    else:
        failures.append(str(asset))
        print(f"  FAIL missing or empty: {asset.relative_to(project_root)}")

if failures:
    raise SystemExit(f"\nEnvironment check failed: {', '.join(failures)}")

print("\nCineIQ environment is ready.")
