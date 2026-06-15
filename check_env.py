import sys
print(f"✅ Python Version: {sys.version[:60]}")

packages = {
    "pandas": "pandas",
    "numpy": "numpy",
    "sklearn": "sklearn",
    "surprise": "surprise",
    "streamlit": "streamlit",
    "fastapi": "fastapi",
    "mlflow": "mlflow",
    "vaderSentiment": "vaderSentiment",
    "transformers": "transformers",
    "torch": "torch"
}

print("\n🔍 Checking installed packages...\n")

for display_name, import_name in packages.items():
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", "OK")
        if display_name == "sklearn":
            ver = mod.__version__
        print(f"✅ {display_name} {ver}")
    except Exception as e:
        print(f"❌ {display_name} — Import failed: {type(e).__name__}")