from fastapi import FastAPI, HTTPException
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.hybrid_recommender import get_hybrid_recommendations, movies, ratings
from src.explain import MovieExplainer
from src.feedback_handler import FeedbackHandler
from api.models import (
    RecommendRequest,
    FeedbackRequest,
    RecommendationResponse,
    MovieRecommendation,
    FeedbackResponse,
    FeedbackStatsResponse,
    HealthResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="CINEIQ API",
    description="Hybrid Movie Recommendation API with Sentiment, Explainability & Feedback",
    version="2.0"
)

print("Loading CINEIQ API resources...")
explainer = MovieExplainer(movies)
feedback_handler = FeedbackHandler()

print("[OK] CINEIQ API ready\n")


# =============== RECOMMENDATIONS ENDPOINTS ===============

@app.get("/", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "CINEIQ Recommendation API is running"
    }


@app.post("/recommend", response_model=RecommendationResponse)
def recommend_movies(request: RecommendRequest):
    """
    Get hybrid recommendations for a user.
    Returns top N movies with scores and explanations.

    Args:
        user_id: User ID (1-162541)
        top_n: Number of recommendations to return (default: 10)

    Returns:
        List of recommendations with explanations and scores
    """
    try:
        if request.user_id < 1 or request.user_id > 162541:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        if request.top_n < 1 or request.top_n > 50:
            raise HTTPException(status_code=400, detail="top_n must be between 1 and 50")

        recommendations = get_hybrid_recommendations(request.user_id, n=request.top_n)

        # Get user's high-rated movies for better explanations
        user_high_rated = ratings[
            (ratings['userId'] == request.user_id) & (ratings['rating'] >= 4.0)
        ]['movieId'].values

        user_high_directors = movies[
            movies['movieId'].isin(user_high_rated)
        ]['director'].dropna().unique().tolist()

        results = []
        for rec in recommendations:
            movie_row = movies[movies['movieId'] == rec['movie_id']].iloc[0]

            explanation = explainer.explain(
                movie_id=rec['movie_id'],
                movie_row=movie_row,
                user_high_rated_movie_ids=list(user_high_rated),
                user_high_rated_directors=user_high_directors
            )

            results.append(MovieRecommendation(
                movie_id=rec['movie_id'],
                title=rec['title'],
                genres=rec['genres'],
                director=rec['director'],
                final_score=rec['final_score'],
                hybrid_score=rec['hybrid_score'],
                sentiment_score=rec['sentiment_score'],
                explanation=explanation
            ))

        return RecommendationResponse(
            user_id=request.user_id,
            total_results=len(results),
            recommendations=results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


# =============== FEEDBACK ENDPOINTS ===============

@app.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback on a recommendation.

    Args:
        user_id: User ID
        movie_id: Movie ID
        movie_title: Movie title
        rating_score: System's predicted rating
        final_score: System's final recommendation score
        feedback: 'like', 'dislike', or 'neutral'
        rating_given: User's manual rating (optional, 1-5)
        comment: User's text comment (optional)

    Returns:
        Success status and message
    """
    try:
        if request.feedback not in ['like', 'dislike', 'neutral']:
            raise HTTPException(status_code=400, detail="feedback must be 'like', 'dislike', or 'neutral'")

        success = feedback_handler.add_feedback(
            user_id=request.user_id,
            movie_id=request.movie_id,
            movie_title=request.movie_title,
            rating_score=request.rating_score,
            final_score=request.final_score,
            feedback=request.feedback,
            rating_given=request.rating_given,
            comment=request.comment
        )

        if success:
            return FeedbackResponse(
                success=True,
                message="Feedback recorded successfully",
                user_id=request.user_id,
                movie_id=request.movie_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to record feedback")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")


@app.get("/feedback/stats", response_model=FeedbackStatsResponse)
def get_feedback_stats():
    """
    Get aggregate feedback statistics.

    Returns:
        Summary statistics of all feedback collected
    """
    try:
        stats = feedback_handler.get_feedback_stats()
        return FeedbackStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving feedback stats: {str(e)}")


@app.get("/feedback/user/{user_id}")
def get_user_feedback(user_id: int):
    """
    Get all feedback for a specific user.

    Args:
        user_id: User ID

    Returns:
        List of feedback records for the user
    """
    try:
        feedback_df = feedback_handler.get_user_feedback(user_id)
        return feedback_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user feedback: {str(e)}")


# =============== METRICS ENDPOINTS ===============

@app.get("/metrics/feedback")
def get_feedback_metrics():
    """
    Get accuracy metrics based on user feedback.

    Returns:
        RMSE, MAE, and correlation between predicted and actual ratings
    """
    try:
        accuracy = feedback_handler.get_accuracy_metrics()
        return accuracy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")


# =============== SYSTEM INFO ===============

@app.get("/info")
def get_system_info():
    """Get system information."""
    return {
        "system": "CINEIQ v2.0",
        "total_movies": len(movies),
        "total_users": ratings['userId'].nunique(),
        "total_ratings": len(ratings),
        "feedback_entries": feedback_handler.get_feedback_stats()['total_feedback']
    }