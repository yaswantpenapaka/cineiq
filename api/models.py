"""
Pydantic models for CINEIQ API
==============================
Request/response schemas for FastAPI endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List


class RecommendRequest(BaseModel):
    """Request schema for getting recommendations."""
    user_id: int
    top_n: int = 10


class FeedbackRequest(BaseModel):
    """Request schema for submitting feedback."""
    user_id: int
    movie_id: int
    movie_title: str
    rating_score: float
    final_score: float
    feedback: str  # 'like', 'dislike', 'neutral'
    rating_given: Optional[float] = None
    comment: str = ""


class MovieRecommendation(BaseModel):
    """Schema for individual movie recommendation."""
    movie_id: int
    title: str
    genres: str
    director: str
    final_score: float
    hybrid_score: float
    sentiment_score: float
    explanation: str


class RecommendationResponse(BaseModel):
    """Response schema for recommendations."""
    user_id: int
    total_results: int
    recommendations: List[MovieRecommendation]


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""
    success: bool
    message: str
    user_id: int
    movie_id: int


class MetricsResponse(BaseModel):
    """Response schema for system metrics."""
    ndcg_at_10: float
    map_at_10: float
    precision_at_10: float
    recall_at_10: float
    diversity: float
    popularity_bias: float
    catalog_coverage: float


class FeedbackStatsResponse(BaseModel):
    """Response schema for feedback statistics."""
    total_feedback: int
    total_users: int
    total_movies: int
    like_count: int
    dislike_count: int
    neutral_count: int
    like_percentage: float
    avg_rating_given: float


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    message: str
