"""
Tests for CineIQ Recommendation Model
======================================
Tests for hybrid recommender, SVD model, and explainability.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hybrid_recommender import get_hybrid_recommendations
from src.explain import MovieExplainer
from src.feedback_handler import FeedbackHandler
from src.metrics import RecommendationMetrics


@pytest.fixture
def movies_df():
    """Load or create sample movies dataframe."""
    BASE_DIR = Path(__file__).parent.parent
    return pd.read_csv(BASE_DIR / "data" / "merged_movies.csv")


@pytest.fixture
def ratings_df():
    """Load or create sample ratings dataframe."""
    BASE_DIR = Path(__file__).parent.parent
    return pd.read_csv(BASE_DIR / "data" / "movielens" / "ratings.csv")


@pytest.fixture
def explainer(movies_df):
    """Create MovieExplainer instance."""
    return MovieExplainer(movies_df)


@pytest.fixture
def feedback_handler():
    """Create FeedbackHandler instance."""
    return FeedbackHandler()


@pytest.fixture
def metrics_evaluator(movies_df, ratings_df):
    """Create RecommendationMetrics instance."""
    return RecommendationMetrics(movies_df, ratings_df)


class TestHybridRecommender:
    """Test hybrid recommendation engine."""

    def test_recommendations_returns_correct_count(self):
        """Hybrid recommender should return correct number of recommendations."""
        user_id = 1
        n = 10

        recs = get_hybrid_recommendations(user_id, n=n)

        assert len(recs) <= n, f"Should return at most {n} recommendations"
        assert len(recs) > 0, "Should return at least 1 recommendation"

    def test_recommendations_have_required_fields(self):
        """Each recommendation should have all required fields."""
        user_id = 1
        recs = get_hybrid_recommendations(user_id, n=5)

        required_fields = ['movie_id', 'title', 'genres', 'director', 'final_score', 'hybrid_score', 'sentiment_score']

        for rec in recs:
            for field in required_fields:
                assert field in rec, f"Missing field: {field}"
                assert rec[field] is not None, f"Field {field} is None"

    def test_recommendations_are_sorted_by_score(self):
        """Recommendations should be sorted by final_score in descending order."""
        user_id = 1
        recs = get_hybrid_recommendations(user_id, n=10)

        scores = [rec['final_score'] for rec in recs]
        assert scores == sorted(scores, reverse=True), "Recommendations should be sorted by score"

    def test_recommendations_scores_in_range(self):
        """Recommendation scores should be in valid range."""
        user_id = 1
        recs = get_hybrid_recommendations(user_id, n=10)

        for rec in recs:
            assert 0 <= rec['final_score'] <= 5, f"Final score out of range: {rec['final_score']}"
            assert 0 <= rec['hybrid_score'] <= 5, f"Hybrid score out of range: {rec['hybrid_score']}"
            assert -1 <= rec['sentiment_score'] <= 1, f"Sentiment score out of range: {rec['sentiment_score']}"

    def test_no_duplicate_recommendations(self):
        """Should not recommend same movie twice."""
        user_id = 1
        recs = get_hybrid_recommendations(user_id, n=20)

        movie_ids = [rec['movie_id'] for rec in recs]
        assert len(movie_ids) == len(set(movie_ids)), "Duplicate recommendations found"

    def test_different_users_different_recommendations(self):
        """Different users should get different recommendations."""
        user1_recs = get_hybrid_recommendations(user_id=1, n=5)
        user2_recs = get_hybrid_recommendations(user_id=2, n=5)

        user1_ids = set(rec['movie_id'] for rec in user1_recs)
        user2_ids = set(rec['movie_id'] for rec in user2_recs)

        # They should not be identical (with high probability)
        assert user1_ids != user2_ids, "Different users got identical recommendations"

    def test_recommendations_exclude_rated_movies(self):
        """Should not recommend movies already rated by user."""
        # This would require accessing internal rated movies set
        # which requires integration testing with actual data
        pass


class TestExplainability:
    """Test explainability module."""

    def test_explanation_not_empty(self, movies_df, explainer):
        """Explanation should not be empty."""
        movie_id = 1
        movie_row = movies_df[movies_df['movieId'] == movie_id].iloc[0]

        explanation = explainer.explain(
            movie_id=movie_id,
            movie_row=movie_row,
            user_high_rated_movie_ids=[],
            user_high_rated_directors=[]
        )

        assert explanation is not None, "Explanation should not be None"
        assert len(explanation) > 0, "Explanation should not be empty"
        assert isinstance(explanation, str), "Explanation should be a string"

    def test_explanation_with_context(self, movies_df, explainer):
        """Explanation should use user context when available."""
        movie_id = 1
        movie_row = movies_df[movies_df['movieId'] == movie_id].iloc[0]

        explanation1 = explainer.explain(
            movie_id=movie_id,
            movie_row=movie_row,
            user_high_rated_movie_ids=[],
            user_high_rated_directors=[]
        )

        explanation2 = explainer.explain(
            movie_id=movie_id,
            movie_row=movie_row,
            user_high_rated_movie_ids=[2, 3, 4],
            user_high_rated_directors=['Director A', 'Director B']
        )

        # Explanations might be different with context
        assert isinstance(explanation1, str), "Explanation should be string"
        assert isinstance(explanation2, str), "Explanation should be string"


class TestFeedbackHandler:
    """Test feedback management system."""

    def test_add_feedback_success(self, feedback_handler):
        """Should successfully add feedback."""
        success = feedback_handler.add_feedback(
            user_id=999,
            movie_id=1,
            movie_title="Test Movie",
            rating_score=3.5,
            final_score=3.8,
            feedback='like',
            rating_given=4.0,
            comment="Great movie!"
        )

        assert success, "Failed to add feedback"

    def test_feedback_invalid_type(self, feedback_handler):
        """Should reject invalid feedback type."""
        success = feedback_handler.add_feedback(
            user_id=999,
            movie_id=1,
            movie_title="Test Movie",
            rating_score=3.5,
            final_score=3.8,
            feedback='maybe',  # Invalid
            rating_given=4.0,
            comment="Test"
        )

        assert not success, "Should reject invalid feedback type"

    def test_get_feedback_stats(self, feedback_handler):
        """Should return valid feedback statistics."""
        stats = feedback_handler.get_feedback_stats()

        required_stats = [
            'total_feedback', 'total_users', 'total_movies',
            'like_count', 'dislike_count', 'neutral_count',
            'like_percentage', 'avg_rating_given'
        ]

        for stat in required_stats:
            assert stat in stats, f"Missing stat: {stat}"
            assert isinstance(stats[stat], (int, float)), f"{stat} should be numeric"

    def test_accuracy_metrics_valid(self, feedback_handler):
        """Should calculate valid accuracy metrics."""
        # Add some feedback first
        feedback_handler.add_feedback(
            user_id=999,
            movie_id=1,
            movie_title="Test",
            rating_score=3.5,
            final_score=3.8,
            feedback='like',
            rating_given=4.0
        )

        accuracy = feedback_handler.get_accuracy_metrics()

        required_metrics = ['total_rated_recommendations', 'rmse', 'mae', 'correlation']

        for metric in required_metrics:
            assert metric in accuracy, f"Missing metric: {metric}"
            assert isinstance(accuracy[metric], (int, float)), f"{metric} should be numeric"


class TestMetricsEvaluation:
    """Test metrics evaluation."""

    def test_system_metrics_valid(self, metrics_evaluator):
        """System metrics should be valid."""
        all_recs = {
            1: [1, 2, 3, 4, 5],
            2: [5, 4, 3, 2, 1],
            3: [2, 3, 4, 5, 1]
        }

        metrics = metrics_evaluator.evaluate_system(all_recs, sample_size=3)

        required = [
            'ndcg@10', 'map@10', 'precision@10', 'recall@10',
            'diversity', 'popularity_bias', 'catalog_coverage'
        ]

        for metric in required:
            assert metric in metrics, f"Missing metric: {metric}"
            assert 0 <= metrics[metric] <= 1, f"{metric} out of range: {metrics[metric]}"

    def test_metrics_reproducible(self, metrics_evaluator):
        """Same recommendations should give same metrics."""
        recs1 = [1, 2, 3, 4, 5]
        recs2 = [1, 2, 3, 4, 5]

        metrics1 = metrics_evaluator.evaluate_recommendations(1, recs1, k=5)
        metrics2 = metrics_evaluator.evaluate_recommendations(1, recs2, k=5)

        assert metrics1 == metrics2, "Same recommendations should give same metrics"


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_recommendation_flow(self):
        """Test complete flow: recommend -> evaluate -> feedback."""
        user_id = 1

        # 1. Get recommendations
        recs = get_hybrid_recommendations(user_id, n=5)
        assert len(recs) > 0, "Should get recommendations"

        # 2. Add feedback
        feedback = FeedbackHandler()
        success = feedback.add_feedback(
            user_id=user_id,
            movie_id=recs[0]['movie_id'],
            movie_title=recs[0]['title'],
            rating_score=recs[0]['final_score'],
            final_score=recs[0]['final_score'],
            feedback='like',
            rating_given=4.0
        )
        assert success, "Should add feedback"

        # 3. Get statistics
        stats = feedback.get_feedback_stats()
        assert stats['total_feedback'] >= 1, "Should have feedback recorded"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
