"""
Fast Sentiment Precomputation with Fuzzy Matching
=================================================
Uses fuzzy string matching for robust IMDB-MovieLens title matching.
Only processes top 5000 popular movies for speed.
"""

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pathlib import Path
import numpy as np
from tqdm import tqdm
from fuzzywuzzy import fuzz

print("=" * 60)
print("Fast Sentiment Precomputation with Fuzzy Matching")
print("=" * 60)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

print("\n[1/5] Loading datasets...")
movies = pd.read_csv(DATA_DIR / "merged_movies.csv")
ratings = pd.read_csv(DATA_DIR / "movielens" / "ratings.csv")
reviews_df = pd.read_csv(DATA_DIR / "imdb/IMDB Dataset.csv")

print(f"   Total movies in dataset : {len(movies)}")
print(f"   Total reviews           : {len(reviews_df)}")

# Step 1: Find Top 5000 most popular movies
print("\n[2/5] Finding Top 5000 most popular movies...")
movie_popularity = ratings.groupby('movieId').size().reset_index(name='rating_count')
top_movies = movie_popularity.nlargest(5000, 'rating_count')['movieId'].values

print(f"   Selected top {len(top_movies)} movies for sentiment computation")

popular_movies = movies[movies['movieId'].isin(top_movies)].copy()

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    if pd.isna(text):
        return 0.0
    return analyzer.polarity_scores(str(text))['compound']

print("\n[3/5] Computing sentiment for all reviews...")
reviews_df['sentiment'] = reviews_df['review'].apply(get_sentiment)

print("\n[4/5] Matching reviews with popular movies (fuzzy matching)...")

movie_sentiments = {}

for idx, row in tqdm(popular_movies.iterrows(), total=len(popular_movies)):
    title = str(row['title'])
    clean_title = title.split('(')[0].strip().lower()

    if len(clean_title) < 3:
        movie_sentiments[row['movieId']] = 0.0
        continue

    # Fuzzy match: find reviews mentioning this movie
    matched_reviews = []
    for review_idx, review in enumerate(reviews_df['review']):
        if pd.isna(review):
            continue
        # Use fuzzy matching with 75 threshold
        score = fuzz.token_set_ratio(clean_title, review.lower())
        if score >= 75:
            matched_reviews.append(review_idx)

    if len(matched_reviews) >= 2:
        sentiments = reviews_df.iloc[matched_reviews]['sentiment'].values
        movie_sentiments[row['movieId']] = float(np.mean(sentiments))
    else:
        movie_sentiments[row['movieId']] = 0.0

# Add sentiment scores to main movies dataframe
movies['sentiment_score'] = movies['movieId'].map(movie_sentiments).fillna(0.0)

print(f"\n   Movies with real sentiment data: {(movies['sentiment_score'] != 0).sum()}")

print("\n[5/5] Saving updated merged_movies.csv...")
movies.to_csv(DATA_DIR / "merged_movies.csv", index=False)

print("\n✅ Sentiment precomputation completed successfully!")
print("=" * 60)