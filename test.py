from src.hybrid_recommender import get_hybrid_recommendations
from src.explain import MovieExplainer
import pandas as pd

print("Testing Hybrid Recommender...\n")

# Test hybrid recommendations
recs = get_hybrid_recommendations(user_id=1, n=5)

print("Top 5 Hybrid Recommendations:")
for r in recs:
    print(f"- {r['title']} | Hybrid Score: {r['hybrid_score']}")

print("\n" + "="*50)

# Test Explainer
print("\nTesting Explainer...")

movies = pd.read_csv("data/merged_movies.csv")
explainer = MovieExplainer(movies)

# Get some user data for explanation
ratings = pd.read_csv("data/movielens/ratings.csv")
user_high_rated = ratings[(ratings['userId'] == 1) & (ratings['rating'] >= 4.0)]['movieId'].values
user_high_directors = movies[movies['movieId'].isin(user_high_rated)]['director'].dropna().unique().tolist()

# Explain the first recommendation
first_movie = recs[0]
movie_row = movies[movies['movieId'] == first_movie['movie_id']].iloc[0]

explanation = explainer.explain(
    movie_id=first_movie['movie_id'],
    movie_row=movie_row,
    user_high_rated_movie_ids=user_high_rated,
    user_high_rated_directors=user_high_directors
)

print(f"\nExplanation for '{first_movie['title']}':")
print(explanation)