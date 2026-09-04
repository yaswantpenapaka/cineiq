"""
Tests for Recommendation Metrics Module
========================================
Unit tests for NDCG, MAP, Precision, Recall, Diversity, Coverage, Popularity Bias
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics import RecommendationMetrics


@pytest.fixture
def sample_movies():
    """Create sample movies dataframe."""
    return pd.DataFrame({
        'movieId': [1, 2, 3, 4, 5],
        'title': ['Movie A', 'Movie B', 'Movie C', 'Movie D', 'Movie E'],
        'genres': ['Action|Sci-Fi', 'Comedy', 'Drama', 'Action', 'Comedy|Drama']
    })


@pytest.fixture
def sample_ratings():
    """Create sample ratings dataframe."""
    return pd.DataFrame({
        'userId': [1, 1, 1, 1, 1, 2, 2, 2],
        'movieId': [1, 2, 3, 4, 5, 1, 2, 3],
        'rating': [4.5, 4.0, 3.5, 2.0, 5.0, 4.0, 3.0, 4.5]
    })


@pytest.fixture
def metrics_evaluator(sample_movies, sample_ratings):
    """Create metrics evaluator instance."""
    return RecommendationMetrics(sample_movies, sample_ratings)


class TestRankingMetrics:
    """Test ranking quality metrics."""

    def test_ndcg_perfect_ranking(self, metrics_evaluator):
        """NDCG should be 1.0 for perfect ranking."""
        relevant = {1, 2, 3}
        recommendations = [1, 2, 3, 4, 5]
        ndcg = metrics_evaluator.ndcg_at_k(recommendations, relevant, k=5)
        assert ndcg == 1.0, "NDCG should be 1.0 for perfect ranking"

    def test_ndcg_worst_ranking(self, metrics_evaluator):
        """NDCG should be lower for poor ranking."""
        relevant = {4, 5}
        recommendations = [1, 2, 3, 4, 5]
        ndcg = metrics_evaluator.ndcg_at_k(recommendations, relevant, k=5)
        assert 0 <= ndcg < 1.0, "NDCG should be between 0 and 1"

    def test_ndcg_range(self, metrics_evaluator):
        """NDCG@k should be in [0, 1]."""
        relevant = {1, 2}
        recommendations = [3, 2, 1, 4, 5]
        ndcg = metrics_evaluator.ndcg_at_k(recommendations, relevant, k=5)
        assert 0 <= ndcg <= 1, "NDCG should be in [0, 1]"

    def test_map_perfect_ranking(self, metrics_evaluator):
        """MAP should be 1.0 for perfect ranking."""
        relevant = {1, 2}
        recommendations = [1, 2, 3, 4, 5]
        map_score = metrics_evaluator.map_at_k(recommendations, relevant, k=5)
        assert map_score == 1.0, "MAP should be 1.0 for perfect ranking"

    def test_precision_at_k(self, metrics_evaluator):
        """Precision@k should correctly count relevant items in top-k."""
        relevant = {1, 2, 3}
        recommendations = [1, 2, 4, 5, 3]
        precision = metrics_evaluator.precision_at_k(recommendations, relevant, k=3)
        # Top-3: [1, 2, 4] -> 2 relevant out of 3
        assert precision == 2/3, f"Expected precision 2/3, got {precision}"

    def test_recall_at_k(self, metrics_evaluator):
        """Recall@k should measure coverage of relevant items."""
        relevant = {1, 2, 3, 4}
        recommendations = [1, 2, 5, 6, 7]
        recall = metrics_evaluator.recall_at_k(recommendations, relevant, k=5)
        # 2 relevant items found in top-5 out of 4 total relevant
        assert recall == 2/4, f"Expected recall 0.5, got {recall}"


class TestDiversityMetrics:
    """Test diversity and coverage metrics."""

    def test_diversity_range(self, metrics_evaluator):
        """Diversity should be in [0, 1]."""
        recommendations = [1, 2, 3, 4, 5]
        diversity = metrics_evaluator.recommendation_diversity(recommendations, k=5)
        assert 0 <= diversity <= 1, "Diversity should be in [0, 1]"

    def test_diversity_single_item(self, metrics_evaluator):
        """Diversity of single item should be 1.0 (no overlap possible)."""
        recommendations = [1]
        diversity = metrics_evaluator.recommendation_diversity(recommendations, k=1)
        assert diversity == 1.0, "Single item should have diversity 1.0"

    def test_catalog_coverage(self, metrics_evaluator):
        """Catalog coverage should be in [0, 1]."""
        all_recs = {1: [1, 2], 2: [3, 4]}
        coverage = metrics_evaluator.catalog_coverage(all_recs, k=2)
        assert 0 <= coverage <= 1, "Coverage should be in [0, 1]"
        assert coverage > 0, "Coverage should be > 0 with recommendations"

    def test_popularity_bias_range(self, metrics_evaluator):
        """Popularity bias should be in [0, 1]."""
        recommendations = [1, 2, 3, 4, 5]
        bias = metrics_evaluator.popularity_bias(recommendations)
        assert 0 <= bias <= 1, "Popularity bias should be in [0, 1]"


class TestAggregateMetrics:
    """Test aggregate metric computation."""

    def test_evaluate_recommendations_returns_all_metrics(self, metrics_evaluator):
        """evaluate_recommendations should return all required metrics."""
        recommendations = [1, 2, 3, 4, 5]
        metrics = metrics_evaluator.evaluate_recommendations(1, recommendations, k=5)

        required_metrics = ['ndcg@10', 'map@10', 'precision@10', 'recall@10', 'diversity', 'popularity_bias']
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
            assert isinstance(metrics[metric], (int, float)), f"{metric} should be numeric"

    def test_evaluate_system_returns_all_metrics(self, metrics_evaluator):
        """evaluate_system should return all required system-level metrics."""
        all_recommendations = {
            1: [1, 2, 3, 4, 5],
            2: [5, 4, 3, 2, 1]
        }
        metrics = metrics_evaluator.evaluate_system(all_recommendations, k=5, sample_size=2)

        required_metrics = [
            'ndcg@10', 'map@10', 'precision@10', 'recall@10',
            'diversity', 'popularity_bias', 'catalog_coverage', 'evaluated_users'
        ]
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_recommendations(self, metrics_evaluator):
        """Handle empty recommendation lists."""
        relevant = {1, 2, 3}
        recommendations = []
        precision = metrics_evaluator.precision_at_k(recommendations, relevant, k=10)
        assert precision == 0.0, "Precision of empty list should be 0"

    def test_no_relevant_items(self, metrics_evaluator):
        """Handle case when user has no relevant items."""
        relevant = set()
        recommendations = [1, 2, 3]
        ndcg = metrics_evaluator.ndcg_at_k(recommendations, relevant, k=3)
        assert ndcg == 0.0, "NDCG with no relevant items should be 0"

    def test_k_larger_than_recommendations(self, metrics_evaluator):
        """Handle k larger than recommendation list."""
        relevant = {1, 2}
        recommendations = [1, 2]
        precision = metrics_evaluator.precision_at_k(recommendations, relevant, k=10)
        # k=10 but only 2 recommendations, precision based on actual k=2
        assert precision == 1.0, "Should handle k > len(recommendations)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
