"""
CINEIQ Evaluation Metrics Module
=================================
Comprehensive metrics for recommendation system evaluation.
Includes ranking metrics, diversity, coverage, and popularity bias.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from typing import List, Dict, Tuple


class RecommendationMetrics:
    """
    Evaluate recommendation system using multiple metrics.
    Metrics include: NDCG, MAP, Precision, Recall, Coverage, Diversity, Popularity Bias.
    """

    def __init__(self, all_movies: pd.DataFrame, ratings_df: pd.DataFrame):
        self.all_movies = all_movies
        self.ratings_df = ratings_df
        self.user_item_matrix = self._build_user_item_matrix()

    def _build_user_item_matrix(self) -> Dict:
        """Build user-item interaction matrix from ratings efficiently."""
        if self.ratings_df.empty:
            return {}
        high_ratings = self.ratings_df[self.ratings_df['rating'] >= 4.0]
        return high_ratings.groupby('userId')['movieId'].apply(set).to_dict()

    # =============== RANKING METRICS ===============
    def ndcg_at_k(self, recommendations: List[int], relevant_items: set, k: int = 10) -> float:
        """
        Normalized Discounted Cumulative Gain @ k
        Measures ranking quality: how high are relevant items ranked?
        Range: 0-1 (1 is perfect)
        """
        # DCG calculation
        dcg = 0.0
        for i, rec in enumerate(recommendations[:k], 1):
            if rec in relevant_items:
                dcg += 1.0 / np.log2(i + 1)

        # Ideal DCG (perfect ranking)
        idcg = sum(1.0 / np.log2(i + 1) for i in range(1, min(k, len(relevant_items)) + 1))

        if idcg == 0:
            return 0.0
        return dcg / idcg

    def map_at_k(self, recommendations: List[int], relevant_items: set, k: int = 10) -> float:
        """
        Mean Average Precision @ k
        Measures: precision at each position where a relevant item is found
        Range: 0-1 (1 is perfect)
        """
        if not relevant_items:
            return 0.0

        precisions = []
        num_relevant = 0

        for i, rec in enumerate(recommendations[:k], 1):
            if rec in relevant_items:
                num_relevant += 1
                precisions.append(num_relevant / i)

        if not precisions:
            return 0.0
        return sum(precisions) / min(k, len(relevant_items))

    def precision_at_k(self, recommendations: List[int], relevant_items: set, k: int = 10) -> float:
        """
        Precision @ k
        Measures: what fraction of top-k recommendations are relevant?
        Range: 0-1 (1 is perfect)
        """
        if k <= 0 or not recommendations:
            return 0.0

        evaluated_recommendations = recommendations[:k]
        relevant_in_top_k = len([r for r in evaluated_recommendations if r in relevant_items])
        return relevant_in_top_k / len(evaluated_recommendations)

    def recall_at_k(self, recommendations: List[int], relevant_items: set, k: int = 10) -> float:
        """
        Recall @ k
        Measures: what fraction of all relevant items are in top-k?
        Range: 0-1 (1 is perfect)
        """
        if not relevant_items:
            return 0.0

        relevant_in_top_k = len([r for r in recommendations[:k] if r in relevant_items])
        return relevant_in_top_k / len(relevant_items)

    # =============== DIVERSITY METRICS ===============
    def recommendation_diversity(self, recommendations: List[int], k: int = 10) -> float:
        """
        Measure how different recommended movies are.
        Uses genre overlap: 1 - avg(genre_overlap)
        Range: 0-1 (1 is most diverse)
        """
        if len(recommendations) <= 1:
            return 1.0

        movies_in_recs = self.all_movies[
            self.all_movies['movieId'].isin(recommendations[:k])
        ]

        if len(movies_in_recs) <= 1:
            return 1.0

        # Calculate genre diversity
        total_overlap = 0
        count = 0

        for i in range(len(movies_in_recs) - 1):
            genres_i = set(str(movies_in_recs.iloc[i]['genres']).split('|'))
            for j in range(i + 1, len(movies_in_recs)):
                genres_j = set(str(movies_in_recs.iloc[j]['genres']).split('|'))
                overlap = len(genres_i & genres_j) / len(genres_i | genres_j) if genres_i | genres_j else 0
                total_overlap += overlap
                count += 1

        avg_overlap = total_overlap / count if count > 0 else 0
        return 1.0 - avg_overlap

    # =============== COVERAGE METRICS ===============
    def catalog_coverage(self, all_recommendations: Dict[int, List[int]], k: int = 10) -> float:
        """
        Percentage of movies that appear in any recommendation.
        Measures: does system recommend diverse movies or same popular ones?
        Range: 0-1 (1 is complete coverage)
        """
        recommended_movies = set()
        for recs in all_recommendations.values():
            recommended_movies.update(recs[:k])

        total_movies = len(self.all_movies)
        return len(recommended_movies) / total_movies if total_movies > 0 else 0.0

    def popularity_bias(self, recommendations: List[int]) -> float:
        """
        Measure popularity bias: does system recommend only popular movies?
        Returns average popularity percentile of recommendations.
        Range: 0-1 (0 = niche movies, 1 = very popular)
        """
        movie_popularity = self.ratings_df.groupby('movieId').size().reset_index(name='count')
        movie_popularity['percentile'] = (
            movie_popularity['count'].rank(pct=True)
        )

        popularity_map = dict(zip(movie_popularity['movieId'], movie_popularity['percentile']))

        rec_popularities = [
            popularity_map.get(rec, 0.5) for rec in recommendations
        ]

        return np.mean(rec_popularities) if rec_popularities else 0.5

    # =============== AGGREGATE METRICS ===============
    def evaluate_recommendations(
        self,
        user_id: int,
        recommendations: List[int],
        k: int = 10
    ) -> Dict[str, float]:
        """
        Compute all metrics for a single user's recommendations.
        """
        relevant_items = self.user_item_matrix.get(user_id, set())

        metrics = {
            'ndcg@10': self.ndcg_at_k(recommendations, relevant_items, k),
            'map@10': self.map_at_k(recommendations, relevant_items, k),
            'precision@10': self.precision_at_k(recommendations, relevant_items, k),
            'recall@10': self.recall_at_k(recommendations, relevant_items, k),
            'diversity': self.recommendation_diversity(recommendations, k),
            'popularity_bias': self.popularity_bias(recommendations),
        }
        return metrics

    def evaluate_system(
        self,
        all_recommendations: Dict[int, List[int]],
        k: int = 10,
        sample_size: int = None
    ) -> Dict[str, float]:
        """
        Compute aggregate metrics across multiple users.
        Sample_size: if None, evaluate all users; else sample random users.
        """
        users_to_eval = list(all_recommendations.keys())

        if sample_size and len(users_to_eval) > sample_size:
            users_to_eval = np.random.choice(users_to_eval, sample_size, replace=False)

        all_ndcg = []
        all_map = []
        all_precision = []
        all_recall = []
        all_diversity = []
        all_popularity_bias = []

        for user_id in users_to_eval:
            recs = all_recommendations[user_id]
            metrics = self.evaluate_recommendations(user_id, recs, k)

            all_ndcg.append(metrics['ndcg@10'])
            all_map.append(metrics['map@10'])
            all_precision.append(metrics['precision@10'])
            all_recall.append(metrics['recall@10'])
            all_diversity.append(metrics['diversity'])
            all_popularity_bias.append(metrics['popularity_bias'])

        # Calculate coverage across all users
        coverage = self.catalog_coverage(all_recommendations, k)

        system_metrics = {
            'ndcg@10': np.mean(all_ndcg),
            'map@10': np.mean(all_map),
            'precision@10': np.mean(all_precision),
            'recall@10': np.mean(all_recall),
            'diversity': np.mean(all_diversity),
            'popularity_bias': np.mean(all_popularity_bias),
            'catalog_coverage': coverage,
            'evaluated_users': len(users_to_eval)
        }

        return system_metrics


def print_metrics(metrics: Dict[str, float]) -> None:
    """Pretty print metrics."""
    print("\n" + "="*50)
    print("RECOMMENDATION METRICS")
    print("="*50)
    for metric_name, value in metrics.items():
        print(f"{metric_name:.<30} {value:.4f}")
    print("="*50 + "\n")
