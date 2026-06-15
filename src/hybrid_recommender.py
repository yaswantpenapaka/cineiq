"""
CINEIQ Hybrid Recommender (Fixed for FastAPI + JSON)
====================================================
All returned values are native Python types (int, float, str).
"""

import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = BASE_DIR / "models" / "svd_model.pkl"

print("Loading Hybrid Recommender (Fixed for API)...")

movies = pd.read_csv(DATA_DIR / "merged_movies.csv")
ratings = pd.read_csv(DATA_DIR / "movielens" / "ratings.csv")

with open(MODEL_PATH, 'rb') as f:
    svd_model = pickle.load(f)

# Build content features
movies['content'] = (
    movies['genres'].fillna('') + ' ' +
    movies['overview'].fillna('') + ' ' +
    movies['keywords'].fillna('')
)

tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
tfidf_matrix = tfidf.fit_transform(movies['content'])

print("Hybrid Recommender ready.\n")


def get_hybrid_recommendations(user_id, n=10, 
                               hybrid_weight=0.8, 
                               sentiment_weight=0.2):
    """
    Hybrid recommendations with proper score normalization + JSON safe types.
    """
    user_rated = set(ratings[ratings['userId'] == user_id]['movieId'].values)
    user_high_rated = ratings[
        (ratings['userId'] == user_id) & (ratings['rating'] >= 4.0)
    ]['movieId'].values

    candidates = []
    for movie_id in movies['movieId'].values:
        if movie_id not in user_rated:
            svd_pred = svd_model.predict(user_id, movie_id).est
            candidates.append({'movie_id': int(movie_id), 'svd_score': float(svd_pred)})

    # Take top 200 by SVD for re-ranking
    candidates = sorted(candidates, key=lambda x: x['svd_score'], reverse=True)[:200]

    final_recs = []

    for cand in candidates:
        movie_id = cand['movie_id']
        svd_score = cand['svd_score']

        # === Content Similarity ===
        try:
            idx = movies[movies['movieId'] == movie_id].index[0]
            movie_vec = tfidf_matrix[idx]
            high_idx = movies[movies['movieId'].isin(user_high_rated)].index

            if len(high_idx) > 0:
                content_sim = float(np.mean(cosine_similarity(movie_vec, tfidf_matrix[high_idx])))
            else:
                content_sim = 0.0
        except:
            content_sim = 0.0

        # Normalize content similarity to rating scale
        normalized_content = 0.5 + (content_sim * 4.5)

        # Hybrid Score
        hybrid_score = (0.7 * svd_score) + (0.3 * normalized_content)

        # Sentiment
        sentiment_row = movies[movies['movieId'] == movie_id]
        sentiment_score = float(sentiment_row['sentiment_score'].values[0]) if not sentiment_row.empty else 0.0

        # Final Score
        final_score = (hybrid_weight * hybrid_score) + (sentiment_weight * max(0, sentiment_score))

        final_recs.append({
            'movie_id': int(movie_id),
            'final_score': float(round(final_score, 3)),
            'hybrid_score': float(round(hybrid_score, 3)),
            'sentiment_score': float(round(sentiment_score, 3))
        })

    # Sort by final score
    final_recs.sort(key=lambda x: x['final_score'], reverse=True)

    # Return top N with movie details (all native Python types)
    results = []
    for rec in final_recs[:n]:
        row = movies[movies['movieId'] == rec['movie_id']].iloc[0]
        results.append({
            'movie_id': int(rec['movie_id']),
            'title': str(row['title']),
            'genres': str(row.get('genres', '')),
            'director': str(row.get('director', 'Unknown')),
            'final_score': rec['final_score'],
            'hybrid_score': rec['hybrid_score'],
            'sentiment_score': rec['sentiment_score']
        })

    return results