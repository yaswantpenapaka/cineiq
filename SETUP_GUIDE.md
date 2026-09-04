# 🚀 CINEIQ Setup & Running Guide

Complete instructions for setting up and running CineIQ with Anaconda/Conda.

---

## 📋 Table of Contents

1. [Option A: Conda Environment Setup](#option-a-conda-environment-setup)
2. [Option B: Docker Setup](#option-b-docker-setup)
3. [Running Individual Components](#running-individual-components)
4. [Running Tests](#running-tests)
5. [Troubleshooting](#troubleshooting)

---

## Option A: Conda Environment Setup

### Step 1: Create Conda Environment

**Using Anaconda Navigator GUI:**

1. Open **Anaconda Navigator**
2. Click **Environments** on the left
3. Click **Create** button
4. Set Name: `cineiq-env`
5. Select Python **3.11** (or 3.10)
6. Click **Create**
7. Wait for installation to complete

**Using Conda Prompt/Terminal:**

```bash
# Create conda environment with Python 3.11
conda create --name cineiq-env python=3.11

# Activate environment
conda activate cineiq-env
```

### Step 2: Install Dependencies

Navigate to project directory:

```bash
# Change to project directory
cd C:\Users\yaswa\cineiq

# Install from requirements.txt
pip install -r requirements.txt
```

Or manually install key packages:

```bash
# Data science
conda install pandas numpy scikit-learn

# ML/Recommendation
pip install scikit-surprise fuzzywuzzy python-Levenshtein

# Sentiment & Explainability
pip install vaderSentiment lime

# Web frameworks
pip install fastapi uvicorn pydantic streamlit plotly

# Testing
pip install pytest pytest-cov

# Utilities
pip install tqdm python-dotenv jupyter ipython
```

### Step 3: Verify Installation

In Conda prompt (with `cineiq-env` activated):

```bash
# Navigate to project
cd C:\Users\yaswa\cineiq

# Run check script
python check_env.py
```

Expected output:
```
✅ Python Version: 3.11.x
✅ pandas
✅ numpy
✅ sklearn
✅ surprise
✅ streamlit
✅ fastapi
✅ vaderSentiment
✅ transformers
```

---

## 🏃 Running Individual Components

### **Option A1: Run Streamlit UI**

```bash
# 1. Open Conda Prompt
# 2. Navigate to project
cd C:\Users\yaswa\cineiq

# 3. Activate environment
conda activate cineiq-env

# 4. Run Streamlit app
streamlit run app/app.py
```

**What happens:**
- Server starts at `http://localhost:8501`
- Browser opens automatically
- Changes reload on save (hot-reload)

**To stop:** Press `Ctrl+C` in terminal

---

### **Option A2: Run FastAPI Backend**

```bash
# 1. Open Conda Prompt
# 2. Navigate to project
cd C:\Users\yaswa\cineiq

# 3. Activate environment
conda activate cineiq-env

# 4. Run API server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**What happens:**
- API server starts at `http://localhost:8000`
- Interactive API docs at `http://localhost:8000/docs`
- Auto-reloads on file changes

**To stop:** Press `Ctrl+C` in terminal

---

### **Option A3: Run Both (Recommended)**

**Using 2 Terminal Windows:**

**Terminal 1 (API):**
```bash
cd C:\Users\yaswa\cineiq
conda activate cineiq-env
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Streamlit):**
```bash
cd C:\Users\yaswa\cineiq
conda activate cineiq-env
streamlit run app/app.py
```

---

### **Option A4: Run Jupyter Notebooks**

```bash
# 1. Activate environment
conda activate cineiq-env

# 2. Navigate to notebooks folder
cd notebooks

# 3. Start Jupyter
jupyter notebook
```

Browser opens at `http://localhost:8888`

---

## Option B: Docker Setup

### Step 1: Install Docker

1. Download [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Install and run Docker
3. Verify: Open PowerShell/CMD and run:
   ```bash
   docker --version
   docker run hello-world
   ```

### Step 2: Build and Run with Docker Compose

```bash
# 1. Navigate to project
cd C:\Users\yaswa\cineiq

# 2. Build images (first time only)
docker-compose build

# 3. Start all services
docker-compose up
```

**What happens:**
- API runs at `http://localhost:8000`
- Streamlit runs at `http://localhost:8501`
- Both services connected via network
- Logs displayed in terminal

**To stop:** Press `Ctrl+C` or in new terminal:
```bash
docker-compose down
```

### Step 3: Docker Quick Commands

```bash
# View running containers
docker ps

# View logs
docker-compose logs -f api
docker-compose logs -f streamlit

# Stop services
docker-compose stop

# Remove containers
docker-compose down

# Remove everything including images
docker-compose down --rmi all

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up
```

---

## 🧪 Running Tests

### Unit Tests - Metrics

```bash
# Activate environment
conda activate cineiq-env

# Navigate to project
cd C:\Users\yaswa\cineiq

# Run metrics tests
pytest tests/test_metrics.py -v

# Run with coverage
pytest tests/test_metrics.py --cov=src.metrics
```

### Unit Tests - Model

```bash
# Run model tests
pytest tests/test_model.py -v

# Run specific test
pytest tests/test_model.py::TestHybridRecommender::test_recommendations_returns_correct_count -v
```

### All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with detailed output
pytest tests/ -v --tb=short

# Generate coverage report
pytest tests/ --cov=src --cov-report=html
# Opens coverage report in htmlcov/index.html
```

---

## 📊 Running Data Preparation Pipeline

### Step 1: Prepare Data (if needed)

```bash
conda activate cineiq-env
cd C:\Users\yaswa\cineiq

# Merge datasets
python src/prepare_data.py

# Expected output:
# [1/5] Loading datasets...
# [2/5] Merging datasets using tmdbId...
# [3/5] Extracting director information...
# [4/5] Extracting top cast...
# [5/5] Cleaning and saving final dataset...
# ✅ Successfully created: data/merged_movies.csv
```

### Step 2: Train Model (if needed)

```bash
# Train SVD model
python src/train_model.py

# Expected output:
# [1/4] Loading ratings data...
# [2/4] Training SVD model...
# [3/4] Evaluating model...
# [4/4] Saving model...
# ✅ Model saved successfully
```

### Step 3: Precompute Sentiment (if needed)

```bash
# Compute sentiment for top 5000 movies
python src/precompute_sentiment.py

# Expected output:
# [1/5] Loading datasets...
# [2/5] Finding top 5000 movies...
# [3/5] Computing sentiment...
# [4/5] Matching reviews...
# [5/5] Saving results...
# ✅ Sentiment precomputation completed
```

---

## 🧪 Testing Model Performance

### Check Recommendations

```bash
conda activate cineiq-env
cd C:\Users\yaswa\cineiq

python test.py
```

**Output:**
```
Testing Hybrid Recommender...

Top 5 Hybrid Recommendations:
- Movie Title 1 | Hybrid Score: 4.23
- Movie Title 2 | Hybrid Score: 4.15
...

Testing Explainer...

Explanation for 'Movie Title 1':
Because it shares themes like: [themes listed]
```

---

## 📈 Viewing Metrics

### In Streamlit UI

1. Start Streamlit: `streamlit run app/app.py`
2. Go to **📊 Your Taste Profile** tab
3. View metrics for specific user

### Via API

```bash
# Get system info
curl http://localhost:8000/info

# Get feedback stats
curl http://localhost:8000/feedback/stats

# Get feedback metrics
curl http://localhost:8000/metrics/feedback
```

### Interactive API Docs

1. Start API: `python -m uvicorn api.main:app --reload`
2. Open browser: `http://localhost:8000/docs`
3. Try endpoints interactively

---

## ⚙️ Environment Variables (Optional)

Create `.env` file in project root:

```
# Flask/Streamlit
DEBUG=True
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit
STREAMLIT_SERVER_PORT=8501
```

---

## 📁 File Structure Reference

```
cineiq/
├── src/
│   ├── prepare_data.py          # Data merging
│   ├── train_model.py           # SVD training
│   ├── hybrid_recommender.py    # Main algorithm
│   ├── explain.py               # Explainability
│   ├── metrics.py               # Evaluation metrics ✨ NEW
│   ├── feedback_handler.py      # Feedback system ✨ NEW
│   └── fuzzy_matcher.py         # String matching ✨ NEW
├── api/
│   ├── main.py                  # FastAPI app (updated)
│   └── models.py                # Pydantic schemas ✨ NEW
├── app/
│   └── app.py                   # Streamlit UI (improved)
├── tests/
│   ├── test_metrics.py          # Metrics tests ✨ NEW
│   └── test_model.py            # Model tests ✨ NEW
├── data/
│   ├── merged_movies.csv
│   ├── movielens/
│   └── imdb/
├── models/
│   └── svd_model.pkl
├── feedback/
│   └── feedback_logs.csv        ✨ NEW (auto-created)
├── requirements.txt             ✨ NEW
├── Dockerfile                   ✨ NEW
├── docker-compose.yml           ✨ NEW
└── SETUP_GUIDE.md               ✨ NEW (this file)
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution:**
```bash
# Make sure you're in project root
cd C:\Users\yaswa\cineiq

# Reinstall from requirements
pip install -r requirements.txt
```

---

### Issue: Port 8000 or 8501 already in use

**Solution:**
```bash
# Change port for Streamlit
streamlit run app/app.py --server.port 8502

# Change port for API
python -m uvicorn api.main:app --port 8001
```

---

### Issue: "No such file or directory: data/merged_movies.csv"

**Solution:**
```bash
# Run data preparation
python src/prepare_data.py
```

---

### Issue: "No module named 'surprise'"

**Solution:**
```bash
pip install scikit-surprise
```

---

### Issue: Docker container exits immediately

**Solution:**
```bash
# Check logs
docker-compose logs api

# Rebuild
docker-compose build --no-cache
docker-compose up
```

---

### Issue: Streamlit throws "streamlit/config.py" error

**Solution:**
```bash
# Clear Streamlit cache
streamlit cache clear

# Reinstall
pip install --upgrade streamlit
```

---

## 📞 Quick Reference

### Conda Commands

| Command | Purpose |
|---------|---------|
| `conda create --name env_name python=3.11` | Create environment |
| `conda activate env_name` | Activate environment |
| `conda deactivate` | Deactivate environment |
| `conda list` | List installed packages |
| `conda remove --name env_name --all` | Delete environment |
| `pip install -r requirements.txt` | Install from file |

### Running Services

| Service | Command | URL |
|---------|---------|-----|
| Streamlit UI | `streamlit run app/app.py` | http://localhost:8501 |
| FastAPI | `python -m uvicorn api.main:app --reload` | http://localhost:8000 |
| API Docs | (with API running) | http://localhost:8000/docs |
| Jupyter | `jupyter notebook` | http://localhost:8888 |

### Testing

| Test | Command |
|------|---------|
| All tests | `pytest tests/ -v` |
| Metrics tests | `pytest tests/test_metrics.py -v` |
| Model tests | `pytest tests/test_model.py -v` |
| With coverage | `pytest tests/ --cov=src` |

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Conda environment created and activated
- [ ] Dependencies installed (`check_env.py` passes)
- [ ] Data files present (data/merged_movies.csv, models/svd_model.pkl)
- [ ] Streamlit runs without errors
- [ ] API starts and docs accessible
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Can get recommendations
- [ ] Can submit feedback
- [ ] Metrics display correctly

---

## 📚 Next Steps

1. **Understand the Model**: Read model_explanation.html
2. **Explore Metrics**: Check metrics in Streamlit UI
3. **Test Features**: Try recommendations and feedback
4. **Run Tests**: Execute pytest tests
5. **Deploy**: Use Docker for containerization

---

## 🎉 You're All Set!

Your CineIQ environment is ready. Start exploring!

```bash
# Favorite command
conda activate cineiq-env
streamlit run app/app.py
```

Happy coding! 🚀
