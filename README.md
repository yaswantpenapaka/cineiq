the data folder consisting of imdb movielens tmdb , is ignored due to their sizes , you can either make them locally available in your folder or acccess them through kaggle/huggingface.

# 🎥 CINEIQ - Personalized Movie Recommendation System

An open, explainable hybrid movie recommendation engine combining **Collaborative Filtering (SVD)**, **Content-based Filtering**, and **Sentiment Analysis** from real reviews.

## Features

- Hybrid Recommendations (SVD + Content + Sentiment)
- Explainability Layer (LIME + Rule-based)
- User Taste Dashboard with Radar Chart
- FastAPI Backend
- Sentiment-Aware Re-ranking using real IMDB reviews

---

## Project Structure
cineiq/
├── data/                  # Datasets (MovieLens, TMDB, IMDB)
├── src/
│   ├── hybrid_recommender.py
│   ├── explain.py
│   ├── precompute_sentiment.py
│   └── train_model.py
├── app/
│   └── app.py             # Streamlit Dashboard
├── api/
│   └── main.py            # FastAPI Backend
├── models/
│   └── svd_model.pkl
├── merged_movies.csv      # Generated file with sentiment scores


go through the document file and install the packages using anaconda prompt .

# 1. Compute sentiment scores (Top 5000 movies)
python src/precompute_sentiment.py

# 2. Train SVD Model (if svd_model.pkl is missing)
python src/train_model.py


How to Run
Option 1: Run Streamlit Dashboard (Recommended for UI)
Bashstreamlit run app/app.py
URL: http://localhost:8501

Option 2: Run FastAPI Backend
Bashuvicorn api.main:app --reload
URL: http://localhost:8000
Interactive Docs: http://localhost:8000/docs

Tech Stack

ML: Surprise (SVD), scikit-learn (TF-IDF + Cosine)
NLP: VADER Sentiment
Frontend: Streamlit + Plotly
Backend: FastAPI
Explainability: LIME + Rule-based
