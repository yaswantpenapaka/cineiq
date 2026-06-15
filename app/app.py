import sys
from pathlib import Path

# Fix for importing from src/
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import pickle
import plotly.graph_objects as go

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.hybrid_recommender import get_hybrid_recommendations
from src.explain import MovieExplainer

st.set_page_config(page_title="CINEIQ", layout="wide")
st.title("🎥 CINEIQ - Personalized Movie Recommendations")

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = BASE_DIR / "models" / "svd_model.pkl"

@st.cache_data
def load_data():
    movies = pd.read_csv(DATA_DIR / "merged_movies.csv")
    ratings = pd.read_csv(DATA_DIR / "movielens" / "ratings.csv")
    return movies, ratings

movies, ratings = load_data()

with open(MODEL_PATH, 'rb') as f:
    svd_model = pickle.load(f)

explainer = MovieExplainer(movies)

# ================== SIDEBAR ==================
st.sidebar.header("User Controls")
user_id = st.sidebar.number_input("Enter User ID", min_value=1, max_value=162541, value=1, step=1)

st.sidebar.markdown("---")
use_sentiment = st.sidebar.checkbox("Apply Sentiment Re-Ranking", value=True)
st.sidebar.caption("Boosts movies with positive real audience reviews")

if st.sidebar.button("Get Recommendations", type="primary"):
    with st.spinner("Generating hybrid recommendations..."):
        
        recommendations = get_hybrid_recommendations(user_id, n=10)
        
        user_high_rated = ratings[
            (ratings['userId'] == user_id) & (ratings['rating'] >= 4.0)
        ]['movieId'].values
        
        user_high_directors = movies[
            movies['movieId'].isin(user_high_rated)
        ]['director'].dropna().unique().tolist()

        st.subheader(f"Top 10 Recommendations for User {user_id}")

        for rec in recommendations:
            movie_row = movies[movies['movieId'] == rec['movie_id']].iloc[0]
            
            reason = explainer.explain(
                movie_id=rec['movie_id'],
                movie_row=movie_row,
                user_high_rated_movie_ids=user_high_rated,
                user_high_rated_directors=user_high_directors
            )

            col1, col2, col3 = st.columns([5, 2.5, 2.5])
            
            with col1:
                st.write(f"**{rec['title']}**")
                st.caption(f"Genres: {rec['genres']}")
            
            with col2:
                st.metric("Final Score", f"{rec['final_score']:.2f}")
                if use_sentiment:
                    st.caption(f"Hybrid: {rec['hybrid_score']} | Sentiment: {rec['sentiment_score']}")
            
            with col3:
                st.write("**Why this movie?**")
                st.caption(reason)
            
            st.divider()

# ================== TASTE DASHBOARD ==================
st.header("Your Taste Profile")

user_ratings = ratings[ratings['userId'] == user_id]
merged = user_ratings.merge(movies, on='movieId', how='left')

col1, col2 = st.columns([1, 2])

with col1:
    st.metric("Total Movies Rated", len(user_ratings))
    avg = user_ratings['rating'].mean() if not user_ratings.empty else 0
    st.metric("Average Rating Given", f"{avg:.2f}")

    if not merged.empty:
        genre_list = merged['genres'].str.split('|').explode()
        genre_counts = genre_list.value_counts().head(8)
        st.subheader("Top Genres")
        st.bar_chart(genre_counts)

with col2:
    st.subheader("Favorite Directors")
    if 'director' in merged.columns:
        director_counts = merged[merged['director'] != "Unknown"]['director'].value_counts().head(8)
        if not director_counts.empty:
            st.bar_chart(director_counts)
        else:
            st.info("Not enough director data available for this user.")
    else:
        st.warning("Director information not found.")

# Radar Chart
st.subheader("Genre Preference Radar")
if not merged.empty:
    genre_list = merged['genres'].str.split('|').explode()
    genre_counts = genre_list.value_counts().head(6)
    
    if len(genre_counts) >= 3:
        categories = genre_counts.index.tolist()
        values = genre_counts.values.tolist()
        categories += [categories[0]]
        values += [values[0]]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='Your Taste'))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# Decade
st.subheader("Movies Watched by Decade")
if not merged.empty:
    decades = merged['title'].str.extract(r'\((\d{4})\)', expand=False).astype(float)
    merged['decade'] = (decades // 10 * 10).astype('Int64')
    decade_counts = merged['decade'].value_counts().sort_index()
    st.bar_chart(decade_counts)