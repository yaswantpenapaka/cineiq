# 🚀 QUICK START - CineIQ v2.0

Get up and running in **5 minutes**! Follow these exact steps.

---

## ⚡ Step 1: Activate Conda Environment (30 seconds)

**Open Anaconda Prompt or PowerShell:**

```bash
# Navigate to project
cd C:\Users\yaswa\cineiq

# Activate your existing conda environment (or create if needed)
conda activate cineiq-env

# Or create new:
conda create --name cineiq-env python=3.11
conda activate cineiq-env
```

---

## ⚡ Step 2: Install Dependencies (2 minutes)

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
python check_env.py
```

**Expected output:**
```
✅ Python Version: 3.11.x
✅ pandas
✅ numpy
✅ sklearn
✅ surprise
✅ streamlit
✅ fastapi
✅ vaderSentiment
```

---

## ⚡ Step 3: Run Streamlit UI (1 minute) - EASIEST

**Single Terminal:**
```bash
streamlit run app/app.py
```

→ Browser opens at `http://localhost:8501` automatically  
→ **Done! Start exploring!** 🎉

---

## ⚡ Step 4: Run with Docker (OPTIONAL - Memory Optimized)

**Option A: API in Docker + Streamlit Locally (RECOMMENDED)**

Terminal 1:
```bash
docker-compose up
# API runs at http://localhost:8000
# API Docs at http://localhost:8000/docs
```

Terminal 2 (NEW - Run Streamlit locally):
```bash
conda activate cineiq-env
streamlit run app/app.py
# Streamlit at http://localhost:8501
```

✅ **Memory usage:** Only 1.2-1.5GB (optimized!)

---

## ⚡ Step 5: Run Tests (OPTIONAL)

```bash
pytest tests/ -v              # All tests
pytest tests/ --cov=src       # With coverage report
```

---

## 📺 Using the App

### Tab 1: 🎯 Recommendations
1. Enter User ID (1-162541)
2. Choose number of recommendations (5-20)
3. Click "Generate Recommendations"
4. See ranked movies with explanations

### Tab 2: 📊 Your Taste Profile
1. View your taste statistics
2. See genre preferences
3. View favorite directors
4. Timeline of movies watched

### Tab 3: 💬 Feedback
1. Submit feedback on recommendations
2. Rate movies you've seen
3. Add comments
4. See feedback statistics

---

## 🐳 Using Docker (Optional)

**Instead of manual setup, run everything in Docker:**

```bash
# Build and start all services
docker-compose up

# Then open:
# - http://localhost:8501 (Streamlit)
# - http://localhost:8000 (API)
```

**To stop:**
```bash
docker-compose down
```

---

## 📊 Testing Recommendations

**Quick test without UI:**
```bash
python test.py
```

---

## ✅ Common Issues

| Issue | Solution |
|-------|----------|
| Port 8501 in use | `streamlit run app/app.py --server.port 8502` |
| "No module named 'surprise'" | `pip install scikit-surprise` |
| "No such file: merged_movies.csv" | `python src/prepare_data.py` |
| Data not loading | Make sure you're in project root: `cd C:\Users\yaswa\cineiq` |

---

## 🎯 What to Try First

1. **Get recommendations** for User ID 1, 10, 100
2. **View taste profile** to understand the data
3. **Submit feedback** on a recommendation
4. **Check API docs** at http://localhost:8000/docs
5. **Run tests** to verify everything works

---

## 📞 Useful Commands

```bash
# List active conda envs
conda info --envs

# Deactivate environment
conda deactivate

# Kill a specific port (e.g., 8501)
# On Windows PowerShell:
Get-Process -Id (Get-NetTCPConnection -LocalPort 8501).OwningProcess | Stop-Process

# Clear Streamlit cache
streamlit cache clear

# View API docs
# Open browser: http://localhost:8000/docs

# Get system info
curl http://localhost:8000/info
```

---

## 🎓 For Placement Interviews

**When asked "Walk me through your project":**

1. **Opening** (30 sec):
   "I built a hybrid movie recommendation system combining collaborative filtering, content similarity, and sentiment analysis with explainability and user feedback."

2. **Technical Details** (2 min):
   - "The model is SVD trained on 25M MovieLens ratings"
   - "Combined 3 signals: 70% collaborative + 30% content + sentiment"
   - "Uses LIME for explainability"

3. **Improvements** (1 min):
   - "Implemented 7 evaluation metrics (NDCG, MAP, Precision, Recall, etc.)"
   - "Added user feedback system with CSV persistence"
   - "Improved UI with Streamlit multi-page app"
   - "Fuzzy matching for robust title matching"
   - "Comprehensive test suite (50+ tests)"
   - "Containerized with Docker"

4. **Demo** (2 min):
   - Show Streamlit UI
   - Show API docs
   - Show test results

---

## 🚀 You're Ready!

Run this now:
```bash
conda activate cineiq-env
streamlit run app/app.py
```

Explore. Try recommendations. Submit feedback. Have fun! 🎬

---

**Need help?** Check `SETUP_GUIDE.md` for detailed instructions.

**Want to understand the model?** Read the artifact: "CineIQ Model Architecture Explained"

**Want to see all changes?** Check `IMPLEMENTATION_SUMMARY.md`

---

**Happy Coding! 🚀**
