from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.hybrid_recommender import get_hybrid_recommendations
from src.explain import MovieExplainer
import pandas as pd

app = FastAPI(
    title="CINEIQ API",
    description="Hybrid Movie Recommendation API with Sentiment & Explainability",
    version="1.0"
)

# Load data once when API starts
BASE_DIR = Path(__file__).parent.parent
movies = pd.read_csv(BASE_DIR / "data" / "merged_movies.csv")
explainer = MovieExplainer(movies)


class RecommendRequest(BaseModel):
    user_id: int
    top_n: int = 10


@app.post("/recommend")
def recommend_movies(request: RecommendRequest):
    """
    Get hybrid recommendations for a user.
    Returns top N movies with scores and explanations.
    """
    try:
        recommendations = get_hybrid_recommendations(request.user_id, n=request.top_n)

        results = []
        for rec in recommendations:
            movie_row = movies[movies['movieId'] == rec['movie_id']].iloc[0]
            
            explanation = explainer.explain(
                movie_id=rec['movie_id'],
                movie_row=movie_row,
                user_high_rated_movie_ids=[],           # Can be improved later
                user_high_rated_directors=[]
            )
            
            results.append({
                "movie_id": rec['movie_id'],
                "title": rec['title'],
                "genres": rec['genres'],
                "director": rec['director'],
                "final_score": rec['final_score'],
                "hybrid_score": rec['hybrid_score'],
                "sentiment_score": rec['sentiment_score'],
                "explanation": explanation
            })

        return {
            "user_id": request.user_id,
            "total_results": len(results),
            "recommendations": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"message": "CINEIQ Recommendation API is running"}